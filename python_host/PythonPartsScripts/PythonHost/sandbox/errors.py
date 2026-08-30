from __future__ import annotations

import traceback
from typing import Annotated, Any

SANDBOX_FILENAME = "<sandbox>"
RESULT_FILENAME = "<sandbox:result_expression>"

ErrorKind = Annotated[str, "Machine readable sandbox failure kind"]

SANDBOX_FILENAMES = frozenset({SANDBOX_FILENAME, RESULT_FILENAME})


def source_line(source: str, lineno: int | None) -> str | None:
    """Return one 1-indexed line of the submitted source"""

    if lineno is None or lineno < 1:
        return None

    lines = source.splitlines()
    if lineno > len(lines):
        return None

    return lines[lineno - 1].rstrip()


def syntax_error_payload(error: SyntaxError, source: str) -> dict[str, Any]:
    """Describe a SyntaxError against the submitted source"""

    return {
        "kind": "syntax_error",
        "type": type(error).__name__,
        "message": error.msg or str(error),
        "lineno": error.lineno,
        "offset": error.offset,
        "line": source_line(source, error.lineno),
    }


def sandbox_frames(error: BaseException, source: str) -> list[dict[str, Any]]:
    """Extract only the frames that belong to submitted sandbox code

    Bridge internals are dropped so the agent sees line numbers that map onto
    the code it actually sent, not onto executor.py.
    """

    frames: list[dict[str, Any]] = []
    for frame in traceback.extract_tb(error.__traceback__):
        if frame.filename not in SANDBOX_FILENAMES:
            continue
        frames.append(
            {
                "lineno": frame.lineno,
                "name": frame.name,
                "line": frame.line or source_line(source, frame.lineno),
            }
        )
    return frames


def runtime_error_payload(
    error: BaseException,
    source: str,
    kind: ErrorKind = "runtime_error",
) -> dict[str, Any]:
    """Describe a runtime failure raised by sandbox code"""

    frames = sandbox_frames(error, source)
    last = frames[-1] if frames else {}
    return {
        "kind": kind,
        "type": type(error).__name__,
        "message": str(error),
        "lineno": last.get("lineno"),
        "line": last.get("line"),
        "frames": frames,
        "traceback": "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        ).strip(),
    }


def validation_error_payload(error: BaseException) -> dict[str, Any]:
    """Describe a rejection from the AST validator"""

    return {
        "kind": "validation_error",
        "type": type(error).__name__,
        "message": str(error),
    }


def timeout_error_payload(error: BaseException, source: str) -> dict[str, Any]:
    """Describe a watchdog abort"""

    payload = runtime_error_payload(error, source, kind="timeout")
    payload["message"] = str(error)
    return payload
