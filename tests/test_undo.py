"""Undo grouping: one agent request should cost the user one undo."""

from __future__ import annotations

import pytest
from PythonHost.undo import undo_step


class Service:
    def __init__(self) -> None:
        self.steps = 0

    def CreateUndoStep(self) -> None:
        self.steps += 1


def test_one_step_is_created_for_the_whole_block():
    service = Service()

    with undo_step(lambda: service) as active:
        assert active is True

    assert service.steps == 1


def test_disabled_creates_no_service_and_reports_inactive():
    built = []

    def factory():
        built.append(1)
        return Service()

    with undo_step(factory, enabled=False) as active:
        assert active is False

    assert built == []


def test_the_step_is_still_created_when_the_body_raises():
    # Code that fails halfway has usually already put elements in the drawing
    # file. Without the step, that partial work is stranded outside the undo
    # stack and the user cannot back it out.
    service = Service()

    with pytest.raises(RuntimeError), undo_step(lambda: service):
        raise RuntimeError("halfway")

    assert service.steps == 1


def test_a_service_without_the_method_does_not_break_the_block():
    class Old:
        pass

    with undo_step(lambda: Old()) as active:
        assert active is True
