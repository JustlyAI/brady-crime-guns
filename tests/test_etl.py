"""Tests for ETL module."""

import pytest
from pathlib import Path


def test_project_structure():
    """Verify project structure is correct."""
    project_root = Path(__file__).parent.parent

    assert (project_root / "src" / "brady" / "__init__.py").exists()
    assert (project_root / "src" / "brady" / "etl" / "__init__.py").exists()
    assert (project_root / "src" / "brady" / "dashboard" / "__init__.py").exists()
    assert (project_root / "pyproject.toml").exists()
    assert (project_root / "requirements.txt").exists()


def test_data_directory_exists():
    """Verify data directories exist."""
    project_root = Path(__file__).parent.parent

    assert (project_root / "data" / "raw").exists()
    assert (project_root / "data" / "processed").exists()
