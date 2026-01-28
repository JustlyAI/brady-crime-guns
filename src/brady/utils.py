"""Shared utilities for Brady Gun Project."""

import os
from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory.

    Order of precedence:
    1. PROJECT_ROOT environment variable (for containers)
    2. Find pyproject.toml by walking up directory tree
    3. Fall back to /app (Railway/Docker default)
    """
    # Check environment variable first (container deployment)
    if env_root := os.environ.get("PROJECT_ROOT"):
        return Path(env_root)

    # Walk up directory tree looking for pyproject.toml
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent

    # Fall back to /app for container environments
    if Path("/app").exists():
        return Path("/app")

    raise RuntimeError("Could not find project root")
