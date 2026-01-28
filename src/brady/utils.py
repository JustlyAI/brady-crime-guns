"""Shared utilities for Brady Gun Project."""

from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory by finding pyproject.toml."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not find project root")
