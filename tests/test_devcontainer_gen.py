"""Behavior tests for the public API of devcontainer_gen."""

from __future__ import annotations

import pytest

import devcontainer_gen


def test_normalize_trims_and_lowercases() -> None:
    assert devcontainer_gen.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        devcontainer_gen.normalize(value)


def test_version_is_semver() -> None:
    parts = devcontainer_gen.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
