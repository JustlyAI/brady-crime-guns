"""
Test Fixtures for Crime Gun DB Integration

CLAUDE CODE INSTRUCTIONS:
=========================

Use these fixtures to write unit tests for the extraction functions.
Create tests in: tests/test_crime_gun_db_extractor.py

Test framework: pytest
Run with: pytest tests/test_crime_gun_db_extractor.py -v
"""

# =============================================================================
# RECOVERY LOCATION TEST CASES (Column R)
# =============================================================================

RECOVERY_LOCATION_FIXTURES = [
    # Simple city, state
    {
        "input": "Sacramento, CA",
        "expected": [{"city": "Sacramento", "state": "CA"}],
        "confidence": "HIGH",
    },
    # Numbered list
    {
        "input": "1. Woodland, CA\n2. Citrus Heights, CA",
        "expected": [
            {"city": "Woodland", "state": "CA"},
            {"city": "Citrus Heights", "state": "CA"},
        ],
        "confidence": "HIGH",
    },
    # With parenthetical note
    {
        "input": "Citrus Heights, CA (Sacramento burb)",
        "expected": [{"city": "Citrus Heights", "state": "CA"}],
        "confidence": "HIGH",
    },
    # Multiple on same line
    {
        "input": "Vacaville, CA; Fairfield, CA",
        "expected": [
            {"city": "Vacaville", "state": "CA"},
            {"city": "Fairfield", "state": "CA"},
        ],
        "confidence": "HIGH",
    },
    # Empty/null
    {
        "input": "",
        "expected": [],
        "confidence": "NONE",
    },
    {
        "input": None,
        "expected": [],
        "confidence": "NONE",
    },
    # State only
    {
        "input": "California",
        "expected": [{"city": None, "state": "CA"}],
        "confidence": "MEDIUM",
    },
]


# =============================================================================
# CASE COURT TEST CASES (Column N)
# =============================================================================

CASE_COURT_FIXTURES = [
    # Standard formats
    {
        "input": "U.S. v. Pangilinan et. al., D. Alaska, No. 20-cr-92",
        "expected": {"court_code": "D. Alaska", "state": "AK", "district": None},
        "confidence": "MEDIUM-HIGH",
    },
    {
        "input": "U.S. v. Smith, E.D. Pa., No. 23-cr-17",
        "expected": {"court_code": "E.D. Pa.", "state": "PA", "district": "Eastern"},
        "confidence": "MEDIUM-HIGH",
    },
    {
        "input": "United States v. Jones (S.D.N.Y.)",
        "expected": {"court_code": "S.D.N.Y.", "state": "NY", "district": "Southern"},
        "confidence": "MEDIUM-HIGH",
    },
    {
        "input": "U.S. v. Doe, N.D. Ill.",
        "expected": {"court_code": "N.D. Ill.", "state": "IL", "district": "Northern"},
        "confidence": "MEDIUM-HIGH",
    },
    # No court reference
    {
        "input": "State v. Johnson",
        "expected": {"court_code": None, "state": None, "district": None},
        "confidence": "NONE",
    },
    # DC
    {
        "input": "U.S. v. Brown, D.D.C.",
        "expected": {"court_code": "D.D.C.", "state": "DC", "district": None},
        "confidence": "MEDIUM-HIGH",
    },
]


# =============================================================================
# TRAFFICKING FLOW TEST CASES (Column P)
# =============================================================================

TRAFFICKING_FLOW_FIXTURES = [
    # Arrow notation
    {
        "input": "AK-->CA",
        "expected": {"source": "AK", "destination": "CA", "dv_flag": False, "swb_flag": False},
        "confidence": "MEDIUM",
    },
    {
        "input": "PA --> NY",
        "expected": {"source": "PA", "destination": "NY", "dv_flag": False, "swb_flag": False},
        "confidence": "MEDIUM",
    },
    # With DV indicator
    {
        "input": "DV* - domestic violence case",
        "expected": {"source": None, "destination": None, "dv_flag": True, "swb_flag": False},
        "confidence": "MEDIUM",
    },
    # With SWB indicator
    {
        "input": "TX-->SWB",
        "expected": {"source": "TX", "destination": "MX", "dv_flag": False, "swb_flag": True},
        "confidence": "MEDIUM",
    },
    # Narrative style (harder to parse)
    {
        "input": "Eagle River man guilty of trafficking firearms from Alaska to California",
        "expected": {"source": "AK", "destination": "CA", "dv_flag": False, "swb_flag": False},
        "confidence": "LOW",
        "note": "Requires NLP or keyword extraction",
    },
    # FFL theft (no flow)
    {
        "input": "FFL theft (22 guns)",
        "expected": {"source": None, "destination": None, "dv_flag": False, "swb_flag": False},
        "confidence": "NONE",
    },
]


# =============================================================================
# TIME-TO-CRIME TEST CASES (Column T)
# =============================================================================

TIME_TO_CRIME_FIXTURES = [
    {"input": "365", "expected": 365},
    {"input": "1095", "expected": 1095},
    {"input": "short", "expected_flag": "SHORT_TTC"},  # < 3 years
    {"input": "< 1 year", "expected_max": 365},
    {"input": "2-3 years", "expected_range": (730, 1095)},
    {"input": None, "expected": None},
    {"input": "", "expected": None},
]


# =============================================================================
# BOOLEAN FIELD TEST CASES
# =============================================================================

BOOLEAN_FIXTURES = [
    {"input": "Yes", "expected": True},
    {"input": "yes", "expected": True},
    {"input": "Y", "expected": True},
    {"input": "y", "expected": True},
    {"input": "TRUE", "expected": True},
    {"input": "true", "expected": True},
    {"input": "1", "expected": True},
    {"input": "X", "expected": True},
    {"input": "x", "expected": True},
    {"input": "No", "expected": False},
    {"input": "no", "expected": False},
    {"input": "N", "expected": False},
    {"input": "FALSE", "expected": False},
    {"input": "0", "expected": False},
    {"input": "", "expected": None},
    {"input": None, "expected": None},
]


# =============================================================================
# FULL ROW TEST CASES
# =============================================================================

FULL_ROW_FIXTURES = [
    {
        "description": "Complete row with all fields",
        "input": {
            "FFL": "Acme Gun Shop",
            "Address": "123 Main St",
            "City": "Fairbanks",
            "State": "AK",
            "license number": "1-23-456-78-9A-12345",
            "2022/23/24 DL2 FFL?": "Yes",
            "Top trace FFL?": "Yes",
            "Revoked FFL?": "No",
            "FFL charged/sued?": "No",
            "Case": "U.S. v. Pangilinan, D. Alaska, No. 20-cr-92",
            "Case subject": "AK-->CA",
            "Location(s) of recovery(ies)": "1. Sacramento, CA\n2. Woodland, CA",
            "Info on recoveries": "Firearms recovered during gang investigation",
            "Time-to-recovery and/or time-to-crime": "365",
            "Facts": "Defendant purchased 15 firearms over 6 months...",
        },
        "expected_jurisdiction": {
            "recovery_city": "Sacramento",  # First location
            "recovery_state": "CA",
            "jurisdiction_method": "EXPLICIT_RECOVERY",
            "jurisdiction_confidence": "HIGH",
        },
    },
    {
        "description": "Row with only case court reference",
        "input": {
            "FFL": "Bob's Guns",
            "City": "Philadelphia",
            "State": "PA",
            "Case": "U.S. v. Smith, E.D. Pa.",
            "Location(s) of recovery(ies)": "",
            "Case subject": "",
        },
        "expected_jurisdiction": {
            "recovery_city": None,
            "recovery_state": "PA",
            "jurisdiction_method": "CASE_COURT",
            "jurisdiction_confidence": "MEDIUM-HIGH",
        },
    },
    {
        "description": "Philadelphia Trace sheet row (implicit jurisdiction)",
        "input": {
            "FFL": "Philly Firearms",
            "sheet_name": "Philadelphia Trace",
        },
        "expected_jurisdiction": {
            "recovery_city": "Philadelphia",
            "recovery_state": "PA",
            "jurisdiction_method": "IMPLICIT",
            "jurisdiction_confidence": "MEDIUM",
        },
    },
]


# =============================================================================
# SAMPLE PYTEST STRUCTURE
# =============================================================================

PYTEST_TEMPLATE = '''
"""
Tests for crime_gun_db_extractor.py

Run: pytest tests/test_crime_gun_db_extractor.py -v
"""

import pytest
from v_2.crime_gun_db_extractor import (
    parse_recovery_locations,
    parse_case_court,
    parse_trafficking_flow,
    parse_time_to_crime,
    convert_boolean_field,
)
from v_2.test_fixtures import (
    RECOVERY_LOCATION_FIXTURES,
    CASE_COURT_FIXTURES,
    TRAFFICKING_FLOW_FIXTURES,
    BOOLEAN_FIXTURES,
)


class TestParseRecoveryLocations:
    @pytest.mark.parametrize("fixture", RECOVERY_LOCATION_FIXTURES)
    def test_parse_recovery_locations(self, fixture):
        result = parse_recovery_locations(fixture["input"])
        assert result == fixture["expected"]


class TestParseCaseCourt:
    @pytest.mark.parametrize("fixture", CASE_COURT_FIXTURES)
    def test_parse_case_court(self, fixture):
        result = parse_case_court(fixture["input"])
        assert result["state"] == fixture["expected"]["state"]


class TestParseTraffickingFlow:
    @pytest.mark.parametrize("fixture", TRAFFICKING_FLOW_FIXTURES)
    def test_parse_trafficking_flow(self, fixture):
        result = parse_trafficking_flow(fixture["input"])
        assert result["source"] == fixture["expected"]["source"]
        assert result["destination"] == fixture["expected"]["destination"]


class TestConvertBooleanField:
    @pytest.mark.parametrize("fixture", BOOLEAN_FIXTURES)
    def test_convert_boolean(self, fixture):
        result = convert_boolean_field(fixture["input"])
        assert result == fixture["expected"]
'''
