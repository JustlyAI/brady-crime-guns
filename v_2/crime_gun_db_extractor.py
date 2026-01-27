"""
Crime Gun Dealer Database Extractor

This module integrates the Crime Gun Dealer Criminal Database into the Brady
Unified Gun Crime Database ETL pipeline.

IMPLEMENTATION INSTRUCTIONS FOR CLAUDE CODE:
============================================

1. DEPENDENCIES: Add spaCy to requirements.txt if implementing NLP extraction:
   - spacy>=3.7.0
   - Run: python -m spacy download en_core_web_sm

2. SHEET PROCESSING ORDER:
   - "CG court doc FFLs" (primary) - full extraction pipeline
   - "Philadelphia Trace" - apply column offset, implicit jurisdiction = Philadelphia, PA
   - "Rochester Trace" - apply column offset, implicit jurisdiction = Rochester, NY
   - "Backdated" - skip if empty
   - "Sheet7" - ALWAYS SKIP

3. DATA QUALITY FILTERS:
   - Skip row 2 (contains "?" placeholder data)
   - Filter rows where FFL column is empty or whitespace-only
   - Handle multi-line FFL names containing "aka"

4. JURISDICTION EXTRACTION PRIORITY:
   Priority 1: parse_recovery_locations() on Column R
   Priority 2: parse_case_court() on Column N
   Priority 3: parse_trafficking_flow() on Column P
   Priority 4: extract_locations_nlp() on Column U (optional)
   Priority 5: Sheet-level implicit jurisdiction

5. INTEGRATION POINT:
   - Import this module in brady_unified_etl.py
   - Call load_and_transform_crime_gun_db() in the main ETL flow
   - Concatenate results with existing unified DataFrame

Source file: data/raw/Crime_Gun_Dealer_DB.xlsx
See PRD: v_2/PRD_Crime_Gun_DB_Integration.md
"""

import re
from pathlib import Path
from typing import Optional

import pandas as pd

# Optional NLP - graceful fallback if not installed
try:
    import spacy
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False


# =============================================================================
# COLUMN MAPPINGS
# =============================================================================

# Main sheet: "CG court doc FFLs"
MAIN_SHEET_COLUMNS = {
    "A": "ffl_name",
    "B": "ffl_premise_street",
    "C": "ffl_premise_city",
    "D": "ffl_premise_state",
    "E": "search_key",
    "F": "ffl_license_number",
    # G: "Which FFL Listing s used" - metadata, skip
    "H": "in_dl2_program",
    "I": "is_top_trace_ffl",
    "J": "is_revoked",
    "K": "is_charged_or_sued",
    # L: "Date Last Checked" - metadata, skip
    # M: "Inspection report?" - skip for now
    "N": "case_reference",
    # O: "Portfolio Created?" - metadata, skip
    "P": "case_subject",
    # Q: "Law enforcement recoveries?" - skip
    "R": "recovery_locations_raw",
    "S": "recovery_info",
    "T": "time_to_crime_raw",
    "U": "facts_narrative",
    # V, W: Notes - skip
}

# Philadelphia/Rochester sheets have column offset (no "Which FFL Listings used")
TRACE_SHEET_COLUMNS = {
    # TODO: Verify exact column mapping by inspecting sheet headers
    # Columns shift by 1 after column F
}

# Federal district court patterns
COURT_PATTERNS = {
    r"D\.\s*Alaska": "AK",
    r"E\.D\.\s*Pa\.?": "PA",
    r"W\.D\.\s*Pa\.?": "PA",
    r"M\.D\.\s*Pa\.?": "PA",
    r"S\.D\.N\.Y\.?": "NY",
    r"E\.D\.N\.Y\.?": "NY",
    r"N\.D\.N\.Y\.?": "NY",
    r"W\.D\.N\.Y\.?": "NY",
    r"N\.D\.\s*Ill\.?": "IL",
    r"C\.D\.\s*Ill\.?": "IL",
    r"S\.D\.\s*Ill\.?": "IL",
    r"C\.D\.\s*Cal\.?": "CA",
    r"N\.D\.\s*Cal\.?": "CA",
    r"S\.D\.\s*Cal\.?": "CA",
    r"E\.D\.\s*Cal\.?": "CA",
    r"D\.D\.C\.?": "DC",
    r"D\.\s*Ariz\.?": "AZ",
    r"D\.\s*Del\.?": "DE",
    r"D\.\s*Nev\.?": "NV",
    # TODO: Add remaining federal districts as encountered
}

# State abbreviation validation
VALID_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU"
}


# =============================================================================
# LOADING FUNCTIONS
# =============================================================================

def load_crime_gun_db(xlsx_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Load all relevant sheets from Crime Gun Dealer DB.

    CLAUDE CODE: Use openpyxl engine. Skip Sheet7 entirely.
    """
    # TODO: Implement
    # sheets_to_load = ["CG court doc FFLs", "Philadelphia Trace", "Rochester Trace", "Backdated"]
    # return {name: pd.read_excel(xlsx_path, sheet_name=name, engine="openpyxl") for name in sheets_to_load}
    raise NotImplementedError("Implement sheet loading with openpyxl")


# =============================================================================
# JURISDICTION EXTRACTION FUNCTIONS
# =============================================================================

def parse_recovery_locations(text: str) -> list[dict]:
    """
    Parse recovery location text from Column R.

    CLAUDE CODE: Handle these patterns:
    - "Sacramento, CA"
    - "1. Woodland, CA\\n2. Citrus Heights, CA"
    - "Vacaville, CA (Solano County)"
    - Multi-line with numbered lists

    Returns list of {"city": str, "state": str} dicts.
    Confidence: HIGH
    """
    # TODO: Implement
    # Pattern: numbered list items, city/state pairs
    # Watch for parenthetical notes like "(Sacramento burb)"
    raise NotImplementedError("Implement recovery location parser")


def parse_case_court(case_text: str) -> dict:
    """
    Extract court jurisdiction from case reference in Column N.

    CLAUDE CODE: Match against COURT_PATTERNS dict.
    Return {"court_code": str, "state": str, "district": str}

    Examples:
    - "U.S. v. Pangilinan, D. Alaska, No. 20-cr-92" -> {"state": "AK", ...}
    - "U.S. v. Smith (E.D. Pa.)" -> {"state": "PA", "district": "Eastern"}

    Confidence: MEDIUM-HIGH
    """
    # TODO: Implement
    raise NotImplementedError("Implement case court parser")


def parse_trafficking_flow(subject_text: str) -> dict:
    """
    Extract trafficking flow from Column P case subject.

    CLAUDE CODE: Handle these patterns:
    - "AK-->CA" -> {"source": "AK", "destination": "CA"}
    - "state(s) --> destination(s)" format
    - Extract "DV*" flag for domestic violence
    - Extract "SWB" flag for southwest border/Mexico

    Confidence: MEDIUM
    """
    # TODO: Implement
    # Regex for arrow patterns: r"([A-Z]{2})\s*-+>\s*([A-Z]{2})"
    raise NotImplementedError("Implement trafficking flow parser")


def extract_locations_nlp(narrative: str) -> list[str]:
    """
    Extract location mentions from narrative text using NLP.

    CLAUDE CODE:
    - Use spaCy en_core_web_sm model
    - Extract GPE (geopolitical entity) labels
    - Filter to US states/cities only
    - Return empty list if spaCy not available

    Confidence: LOW-MEDIUM (flag results for review)
    """
    if not NLP_AVAILABLE:
        return []

    # TODO: Implement
    # nlp = spacy.load("en_core_web_sm")
    # doc = nlp(narrative)
    # return [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    raise NotImplementedError("Implement NLP location extraction")


def determine_jurisdiction(row: pd.Series) -> dict:
    """
    Apply jurisdiction extraction priority chain to a single row.

    CLAUDE CODE: Try extractors in order, return first successful result
    with confidence level and method used.

    Returns: {
        "recovery_city": str | None,
        "recovery_state": str | None,
        "jurisdiction_method": str,  # EXPLICIT_RECOVERY | CASE_COURT | TRAFFICKING_FLOW | NLP | IMPLICIT
        "jurisdiction_confidence": str  # HIGH | MEDIUM | LOW
    }
    """
    # TODO: Implement priority chain
    raise NotImplementedError("Implement jurisdiction priority chain")


# =============================================================================
# TRANSFORMATION FUNCTIONS
# =============================================================================

def clean_ffl_name(name: str) -> str:
    """Normalize FFL name, handle 'aka' patterns."""
    # TODO: Implement
    raise NotImplementedError("Implement FFL name cleaning")


def parse_time_to_crime(ttc_raw: str) -> Optional[int]:
    """
    Parse time-to-crime to integer days.

    CLAUDE CODE: Handle various formats:
    - Integer: "365" -> 365
    - Text: "short" -> flag as <1095
    - Range: "1-2 years" -> estimate midpoint in days
    """
    # TODO: Implement
    raise NotImplementedError("Implement TTC parser")


def convert_boolean_field(value) -> Optional[bool]:
    """Convert various boolean representations to Python bool."""
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower().strip() in ("yes", "y", "true", "1", "x")
    return bool(value)


def transform_to_unified(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """
    Transform Crime Gun DB sheet to unified schema.

    CLAUDE CODE:
    1. Apply column mapping based on sheet_name
    2. Run jurisdiction extraction on each row
    3. Add source traceability fields
    4. Validate state codes against VALID_STATES
    """
    # TODO: Implement
    raise NotImplementedError("Implement unified schema transformation")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def load_and_transform_crime_gun_db(xlsx_path: str | Path) -> pd.DataFrame:
    """
    Main entry point: Load Crime Gun DB and transform to unified schema.

    CLAUDE CODE: This is the function to call from brady_unified_etl.py

    Args:
        xlsx_path: Path to Crime_Gun_Dealer_DB.xlsx

    Returns:
        DataFrame in unified schema format, ready to concatenate with
        other data sources.
    """
    # TODO: Implement
    # 1. Load sheets
    # 2. Transform each sheet
    # 3. Concatenate results
    # 4. Add source_dataset = "CRIME_GUN_DB"
    raise NotImplementedError("Implement main entry point")


if __name__ == "__main__":
    # Quick test
    import sys
    if len(sys.argv) > 1:
        xlsx_path = sys.argv[1]
        df = load_and_transform_crime_gun_db(xlsx_path)
        print(f"Loaded {len(df)} records")
        print(df.head())
    else:
        print("Usage: python crime_gun_db_extractor.py <path_to_xlsx>")
