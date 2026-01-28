"""Tests for ETL module."""

import pytest
from pathlib import Path

from brady.etl.process_gunstat import parse_ffl_field, parse_case_field, parse_firearm_field


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


# Tests for parse_ffl_field()

def test_parse_ffl_field_complete():
    """Test parsing a complete FFL field."""
    text = "Cabela's\nNewark, DE\nFFL 8-51-01809"
    result = parse_ffl_field(text)

    assert result['dealer_name'] == "Cabela's"
    assert result['dealer_city'] == "Newark"
    assert result['dealer_state'] == "DE"
    assert result['dealer_ffl'] == "8-51-01809"


def test_parse_ffl_field_missing_data():
    """Test parsing with missing components."""
    text = "Some Dealer\nPhiladelphia, PA"
    result = parse_ffl_field(text)

    assert result['dealer_name'] == "Some Dealer"
    assert result['dealer_city'] == "Philadelphia"
    assert result['dealer_state'] == "PA"
    assert result['dealer_ffl'] is None


def test_parse_ffl_field_none():
    """Test parsing None/NaN input."""
    import pandas as pd

    result = parse_ffl_field(None)
    assert result['dealer_name'] is None
    assert result['dealer_city'] is None
    assert result['dealer_state'] is None
    assert result['dealer_ffl'] is None

    result = parse_ffl_field(pd.NA)
    assert result['dealer_name'] is None


# Tests for parse_case_field()

def test_parse_case_field_complete():
    """Test parsing complete case info."""
    text = "Jason Miles\nCase #:30-23-063056"
    result = parse_case_field(text)

    assert result['defendant_name'] == "Jason Miles"
    assert result['case_number'] == "30-23-063056"


def test_parse_case_field_none():
    """Test parsing None input."""
    result = parse_case_field(None)

    assert result['defendant_name'] is None
    assert result['case_number'] is None


def test_parse_case_field_no_case_number():
    """Test parsing without case number."""
    text = "John Doe"
    result = parse_case_field(text)

    assert result['defendant_name'] == "John Doe"
    assert result['case_number'] is None


# Tests for parse_firearm_field()

def test_parse_firearm_field_complete():
    """Test parsing complete firearm info."""
    text = "Taurus G2C #ABE573528\npurchased 7/2/20 by Bobby Cooks Jr"
    result = parse_firearm_field(text)

    assert result['manufacturer'] == "TAURUS"
    assert result['serial'] == "ABE573528"
    assert result['purchase_date'] == "7/2/20"
    assert result['purchaser'] == "Bobby Cooks Jr"


def test_parse_firearm_field_manufacturers():
    """Test manufacturer name standardization."""
    # Test S&W -> SMITH & WESSON
    result = parse_firearm_field("S&W M&P #ABC123")
    assert result['manufacturer'] == "SMITH & WESSON"

    # Test GLOCK
    result = parse_firearm_field("Glock 19 #XYZ789")
    assert result['manufacturer'] == "GLOCK"

    # Test SIG -> SIG SAUER
    result = parse_firearm_field("Sig P365 #DEF456")
    assert result['manufacturer'] == "SIG SAUER"


def test_parse_firearm_field_none():
    """Test parsing None input."""
    result = parse_firearm_field(None)

    assert result['manufacturer'] is None
    assert result['serial'] is None
    assert result['purchase_date'] is None
    assert result['purchaser'] is None


def test_parse_firearm_field_caliber():
    """Test caliber extraction."""
    result = parse_firearm_field("Glock 19 9mm #ABC123")
    assert result['caliber'] == "9mm"

    result = parse_firearm_field("Ruger LCP .380 #DEF456")
    assert result['caliber'] == ".380"
