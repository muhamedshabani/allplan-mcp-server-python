"""Group a batch of Allplan changes into a single undo step.

Allplan creates one undo step per ``CreateElements`` call by default. An agent
that places a forty bar rebar cage would therefore leave forty undo steps, and
backing that out by hand is miserable. The bridge instead suppresses the per
call step and closes one step around the whole request.

This module imports nothing from Allplan; the handler passes a factory that
builds the real ``AllplanIFW.UndoRedoService``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Annotated, Any

UndoServiceFactory = Annotated[Callable[[], Any], "Builds an Allplan UndoRedoService"]


@contextmanager
def undo_step(factory: UndoServiceFactory, enabled: bool = True) -> Iterator[bool]:
    """Close one undo step around a batch of document changes

    Yields whether the step is active, so callers can pass ``createUndoStep``
    accordingly.

    The step is created even when the body raises. Code that fails halfway has
    usually already put elements in the drawing file, and the user needs one
    undo to get rid of them. Swallowing the step on failure would strand that
    work outside the undo stack.
    """

    if not enabled:
        yield False
        return

    service = factory()
    try:
        yield True
    finally:
        create = getattr(service, "CreateUndoStep", None)
        if create is not None:
            create()
