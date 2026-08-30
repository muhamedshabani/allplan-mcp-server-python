from __future__ import annotations

import time

import pytest
from PythonHost.sandbox.limits import (
    DeadlineWatchdog,
    SandboxLimits,
    SandboxTimeoutError,
    TruncatingStringIO,
)


def test_stringio_keeps_output_under_the_cap() -> None:
    buffer = TruncatingStringIO(max_chars=100)
    buffer.write("hello")

    assert buffer.getvalue() == "hello"
    assert buffer.truncated is False


def test_stringio_truncates_at_the_cap() -> None:
    buffer = TruncatingStringIO(max_chars=10)
    buffer.write("a" * 25)

    assert buffer.getvalue() == "a" * 10
    assert buffer.truncated is True


def test_stringio_reports_full_length_so_print_does_not_break() -> None:
    buffer = TruncatingStringIO(max_chars=4)

    # print() checks the return value of write(); returning the truncated count
    # would make it raise. It must report what the caller handed over.
    assert buffer.write("abcdefgh") == 8
    assert buffer.write("more") == 4


def test_watchdog_aborts_an_unbounded_loop() -> None:
    started = time.monotonic()

    with pytest.raises(SandboxTimeoutError), DeadlineWatchdog(timeout_seconds=0.25):
        while True:
            pass

    assert time.monotonic() - started < 5


def test_watchdog_leaves_fast_code_alone() -> None:
    with DeadlineWatchdog(timeout_seconds=5):
        total = sum(range(1000))

    assert total == 499500


def test_watchdog_restores_the_previous_trace_function() -> None:
    import sys

    before = sys.gettrace()
    with DeadlineWatchdog(timeout_seconds=5):
        pass

    assert sys.gettrace() is before


def test_limits_reject_nonsense_budgets() -> None:
    with pytest.raises(ValueError):
        SandboxLimits(timeout_seconds=0).validate()

    with pytest.raises(ValueError):
        SandboxLimits(max_stdout_chars=-1).validate()
