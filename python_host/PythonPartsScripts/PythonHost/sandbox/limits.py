from __future__ import annotations

import io
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from types import FrameType
from typing import Annotated, Any

Seconds = Annotated[float, "Wall clock budget in seconds"]
ByteCount = Annotated[int, "Character budget"]


DEFAULT_TIMEOUT_SECONDS: Seconds = 10.0
DEFAULT_MAX_STDOUT_CHARS: ByteCount = 64_000
DEFAULT_MAX_RESULT_CHARS: ByteCount = 64_000
DEFAULT_MAX_RESULT_ITEMS: ByteCount = 5_000


class SandboxTimeoutError(Exception):
    """Raised when sandbox code exceeds its wall clock budget"""


@dataclass(frozen=True)
class SandboxLimits:
    """Hold the runtime budgets applied to one sandbox execution"""

    timeout_seconds: Seconds = DEFAULT_TIMEOUT_SECONDS
    max_stdout_chars: ByteCount = DEFAULT_MAX_STDOUT_CHARS
    max_result_chars: ByteCount = DEFAULT_MAX_RESULT_CHARS
    max_result_items: ByteCount = DEFAULT_MAX_RESULT_ITEMS

    def validate(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")
        if self.max_stdout_chars <= 0:
            raise ValueError("max_stdout_chars must be greater than zero.")
        if self.max_result_chars <= 0:
            raise ValueError("max_result_chars must be greater than zero.")
        if self.max_result_items <= 0:
            raise ValueError("max_result_items must be greater than zero.")


class TruncatingStringIO(io.TextIOBase):
    """Collect stdout up to a character budget, then drop the rest

    Sandbox code that prints in a loop should not be able to grow the MCP
    response without bound. Output past the budget is discarded instead of
    raising, so a noisy script still returns whatever it produced before the
    cap. Runaway loops are stopped by the deadline watchdog, not by this class.
    """

    def __init__(self, max_chars: ByteCount) -> None:
        super().__init__()
        self.max_chars = max_chars
        self.truncated = False
        self._chunks: list[str] = []
        self._length = 0

    def write(self, text: str) -> int:
        written = len(text)
        if self._length >= self.max_chars:
            self.truncated = True
            return written

        remaining = self.max_chars - self._length
        if written > remaining:
            self._chunks.append(text[:remaining])
            self._length = self.max_chars
            self.truncated = True
            return written

        self._chunks.append(text)
        self._length += written
        return written

    def writable(self) -> bool:
        return True

    def getvalue(self) -> str:
        return "".join(self._chunks)


class DeadlineWatchdog:
    """Abort sandbox code once a wall clock deadline passes

    Implemented with ``sys.settrace``, so the deadline is only checked between
    Python bytecode lines. A single long running call into a native Allplan API
    cannot be interrupted, and neither can a blocking C level call. This stops
    the common failure - a generated ``while True`` freezing the Allplan UI
    thread - but it is not a hard kill.
    """

    def __init__(self, timeout_seconds: Seconds) -> None:
        self.timeout_seconds = timeout_seconds
        self.expired = False
        self._deadline = 0.0
        self._previous_trace: Callable[..., Any] | None = None
        self._caller: FrameType | None = None

    def __enter__(self) -> DeadlineWatchdog:
        self._deadline = time.monotonic() + self.timeout_seconds
        self._previous_trace = sys.gettrace()
        sys.settrace(self._trace)

        # settrace only arms frames created after this point. The frame that
        # opened the context manager already exists, so a loop written directly
        # inside it would never be traced. Arm it explicitly.
        caller = sys._getframe(1)
        caller.f_trace_lines = True
        caller.f_trace = self._trace

        self._caller = caller
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        sys.settrace(self._previous_trace)
        if self._caller is not None:
            self._caller.f_trace = None
            self._caller = None

    def _trace(self, frame: FrameType, event: str, arg: Any) -> Callable[..., Any] | None:
        if time.monotonic() > self._deadline:
            self.expired = True
            raise SandboxTimeoutError(
                f"execute_python exceeded its {self.timeout_seconds:g}s time budget."
            )

        frame.f_trace_lines = True
        return self._trace
