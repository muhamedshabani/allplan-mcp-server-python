"""Utility helper template

Copy only the helpers you need
Do not turn this folder into a shared runtime package
"""

from __future__ import annotations

from math import isfinite


def validate_finite(value: float, name: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def validate_positive(value: float, name: str) -> float:
    number = validate_finite(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def validate_count(value: int, name: str = "count") -> int:
    count = int(value)
    if count < 1:
        raise ValueError(f"{name} must be at least one")
    return count


def load_runtime_pattern() -> None:
    # Keep ALLPLAN imports inside create_element or another runtime boundary
    # Example
    # import NemAll_Python_Geometry as AllplanGeo
    # import NemAll_Python_Reinforcement as AllplanReinf
    # from CreateElementResult import CreateElementResult
    # from TypeCollections.ModelEleList import ModelEleList
    raise NotImplementedError("Template only")
