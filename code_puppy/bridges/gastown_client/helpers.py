"""Shared helper utilities for gastown_client mixins."""

from __future__ import annotations

from enum import Enum
from typing import TypeVar

from pydantic import BaseModel

from code_puppy.bridges.gastown_client.exceptions import GastownError
from code_puppy.bridges.gastown_client.models import CommandResult

E = TypeVar("E", bound=Enum)
M = TypeVar("M", bound=BaseModel)


def coerce_enum(value: E | str, enum_cls: type[E], label: str = "value") -> E:
    """Coerce a string to an enum value."""
    if isinstance(value, str):
        try:
            return enum_cls(value.lower())
        except ValueError:
            raise GastownError(f"Invalid {label}: {value}")
    return value


def parse_model_list(
    result: CommandResult,
    model: type[M],
    key: str,
) -> list[M]:
    """Parse a command result into a list of Pydantic models."""
    data = result.parsed_output
    if isinstance(data, list):
        return [model.model_validate(item) for item in data]
    if isinstance(data, dict) and key in data:
        return [model.model_validate(item) for item in data[key]]
    return []


def validate_options(options: dict, allowlist: frozenset[str], context: str) -> None:
    """Raise on unrecognised ``**options`` keys.

    Args:
        options: The kwargs dict to check.
        allowlist: Permitted key names.
        context: Label used in the error message (e.g. "convoy_create").
    """
    bad = set(options) - allowlist
    if bad:
        raise GastownError(f"Unknown {context} options: {', '.join(sorted(bad))}")
