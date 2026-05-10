"""API reference lookup template

Use this as a reminder for what to confirm before generating code
This file is guidance only
"""

from __future__ import annotations


def checklist() -> list[str]:
    return [
        "Confirm the module name",
        "Confirm the constructor signature",
        "Confirm the enum names used by the call",
        "Confirm whether the API is version specific",
        "Feed only the needed definitions back into the generated PythonPart",
    ]
