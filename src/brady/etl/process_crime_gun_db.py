#!/usr/bin/env python3
"""
Brady ETL - Process Crime Gun Dealer Database

Processes Crime_Gun_Dealer_DB.xlsx and outputs to SQLite.
Dataset contains court case records linking FFLs to crime guns.
"""

import re
import sqlite3

import pandas as pd
from termcolor import cprint

from brady.etl.database import get_db_path, migrate_add_crime_gun_db_columns
from brady.utils import get_project_root


# Recovery location - handles hyphens, apostrophes, periods in city names
# Examples: "Sacramento, CA", "St. Louis, MO", "Winston-Salem, NC"
_RECOVERY_PATTERN = re.compile(
    r"(?:\d+\.\s*)?([A-Za-z][A-Za-z\s\.\-']+?),\s*([A-Z]{2})(?:\s|$|\))"
)

# Trafficking flow: "AK-->CA", "TX->SWB"
# Match SWB first since it's 3 chars, then fall back to 2-char state codes
_FLOW_PATTERN = re.compile(r"([A-Z]{2})\s*(?:--?>|==?>)\s*(SWB|[A-Z]{2})")

# Federal court abbreviation to state code mapping
COURT_STATE_MAP = {
    "Alaska": "AK",
    "Ariz.": "AZ",
    "Cal.": "CA",
    "Colo.": "CO",
    "Conn.": "CT",
    "Del.": "DE",
    "Fla.": "FL",
    "Ga.": "GA",
    "Ill.": "IL",
    "Ind.": "IN",
    "Kan.": "KS",
    "Ky.": "KY",
    "La.": "LA",
    "Mass.": "MA",
    "Md.": "MD",
    "Mich.": "MI",
    "Minn.": "MN",
    "Mo.": "MO",
    "N.J.": "NJ",
    "N.Y.": "NY",
    "N.C.": "NC",
    "Ohio": "OH",
    "Okla.": "OK",
    "Or.": "OR",
    "Pa.": "PA",
    "Tenn.": "TN",
    "Tex.": "TX",
    "Va.": "VA",
    "Wash.": "WA",
    "W.Va.": "WV",
    "Wis.": "WI",
}


def parse_recovery_location(text) -> tuple[str, str] | None:
    """Extract first (city, state) from recovery location text."""
    if not text or pd.isna(text):
        return None
    match = _RECOVERY_PATTERN.search(str(text))
    if match:
        return (match.group(1).strip(), match.group(2))
    return None


def parse_court_state(text) -> str | None:
    """Extract state code from federal court reference."""
    if not text or pd.isna(text):
        return None
    text = str(text)
    for abbrev, state_code in COURT_STATE_MAP.items():
        if abbrev in text:
            return state_code
    return None


def parse_trafficking_flow(text) -> tuple[str, str] | None:
    """Extract (origin, destination) from trafficking flow text."""
    if not text or pd.isna(text):
        return None
    match = _FLOW_PATTERN.search(str(text).upper())
    if match:
        return (match.group(1), match.group(2))
    return None


def convert_boolean(value) -> bool | None:
    """Convert Yes/No/True/False to boolean. Unknown = None."""
    if pd.isna(value):
        return None
    val = str(value).strip().lower()
    if val in ("yes", "true", "1"):
        return True
    if val in ("no", "false", "0"):
        return False
    return None


def parse_time_to_crime(text) -> int | None:
    """Parse time-to-crime to integer days. Unknown = None."""
    if not text or pd.isna(text):
        return None
    text = str(text).lower().strip()
    # Handle months first (check before days since "5" would match days pattern)
    match = re.search(r"(\d+)\s*months?", text)
    if match:
        return int(match.group(1)) * 30
    # Try to extract number of days
    match = re.search(r"(\d+)\s*(?:days?)?", text)
    if match:
        return int(match.group(1))
    return None


def get_jurisdiction(
    row: pd.Series, sheet_name: str
) -> tuple[str | None, str | None, str]:
    """
    Get jurisdiction using priority chain. Returns (state, city, method).

    Priority:
    1. Recovery location (Column R)
    2. Court reference (Column N)
    3. Trafficking destination (Column P)
    4. Sheet default (Philadelphia=PA, Rochester=NY)
    5. Dealer state (Column D)
    """
    # Priority 1: Recovery location
    recovery_col = "Location(s) of recovery(ies)"
    if recovery_col in row.index:
        recovery = parse_recovery_location(row.get(recovery_col))
        if recovery:
            return (recovery[1], recovery[0], "RECOVERY")

    # Priority 2: Court reference
    case_col = "Case"
    if case_col in row.index:
        court_state = parse_court_state(row.get(case_col))
        if court_state:
            return (court_state, None, "COURT")

    # Priority 3: Trafficking destination
    # Column 15 has the long name with the case subject info
    case_subject = None
    for col in row.index:
        if "Case subject" in str(col):
            case_subject = row[col]
            break

    if case_subject is not None:
        try:
            if not pd.isna(case_subject):
                flow = parse_trafficking_flow(case_subject)
                if flow and flow[1] != "SWB":
                    return (flow[1], None, "TRAFFICKING")
        except (ValueError, TypeError):
            pass

    # Priority 4: Sheet default
    if "Philadelphia" in sheet_name:
        return ("PA", "Philadelphia", "SHEET_DEFAULT")
    if "Rochester" in sheet_name:
        return ("NY", "Rochester", "SHEET_DEFAULT")

    # Priority 5: Dealer state
    dealer_state = row.get("State")
    if dealer_state and not pd.isna(dealer_state):
        return (str(dealer_state).strip().upper(), None, "DEALER_STATE")

    return (None, None, "UNKNOWN")


def transform_row(row: pd.Series, sheet_name: str, source_row: int) -> dict | None:
    """Transform a single row to unified schema."""
    # Skip garbage rows
    ffl_name = row.get("FFL")
    if ffl_name is None or pd.isna(ffl_name) or str(ffl_name).strip() in ("?", ""):
        return None

    # Get jurisdiction
    state, city, method = get_jurisdiction(row, sheet_name)

    # Parse trafficking flow from case subject column
    case_subject = None
    for col in row.index:
        if "Case subject" in str(col):
            case_subject = row[col]
            break

    flow = parse_trafficking_flow(case_subject)

    # Get time-to-crime column (column 19)
    time_to_crime_raw = None
    for col in row.index:
        if "Time-to-recovery" in str(col) or "time-to-crime" in str(col).lower():
            time_to_crime_raw = row[col]
            break

    # Get facts column
    facts = row.get("Facts")

    return {
        "source_dataset": "CRIME_GUN_DB",
        "source_sheet": sheet_name,
        "source_row": source_row,
        "jurisdiction_state": state,
        "jurisdiction_city": city,
        "jurisdiction_method": method,
        "dealer_name": str(ffl_name).strip() if ffl_name else None,
        "dealer_city": row.get("City"),
        "dealer_state": row.get("State"),
        "dealer_ffl": row.get("license number"),
        "in_dl2_program": convert_boolean(row.get("2022/23/24 DL2 FFL?")),
        "is_top_trace_ffl": convert_boolean(row.get("Top trace FFL?")),
        "is_revoked": convert_boolean(row.get("Revoked FFL?")),
        "is_charged_or_sued": convert_boolean(row.get("FFL charged/sued?")),
        "case_name": row.get("Case"),
        "trafficking_origin": flow[0] if flow else None,
        "trafficking_destination": flow[1] if flow else None,
        "is_southwest_border": flow[1] == "SWB" if flow else False,
        "time_to_crime": parse_time_to_crime(time_to_crime_raw),
        "facts_narrative": facts if facts is not None and pd.notna(facts) else None,
    }


def main():
    """
    Main entry point for Crime Gun DB ETL.

    Usage:
        uv run python -m brady.etl.process_crime_gun_db
    """
    cprint("=" * 60, "cyan")
    cprint("PROCESSING CRIME GUN DEALER DATABASE", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")

    root = get_project_root()
    xlsx_path = root / "data" / "raw" / "Crime_Gun_Dealer_DB.xlsx"
    db_path = get_db_path()

    if not xlsx_path.exists():
        cprint(f"ERROR: Input file not found: {xlsx_path}", "red")
        return None

    # Run migration to ensure columns exist
    cprint("Running database migration...", "yellow")
    migrate_add_crime_gun_db_columns(db_path)

    # Load sheets (skip Sheet7, Backdated, Rochester Trace - empty)
    cprint(f"\nLoading: {xlsx_path}", "green")
    xlsx = pd.ExcelFile(xlsx_path)
    skip_sheets = {"Sheet7", "Backdated"}

    all_records = []
    sheet_stats = {}

    for sheet_name in xlsx.sheet_names:
        if sheet_name in skip_sheets:
            cprint(f"  Skipping sheet: {sheet_name}", "yellow")
            continue

        df = pd.read_excel(xlsx, sheet_name=sheet_name)
        if df.empty:
            cprint(f"  Empty sheet: {sheet_name}", "yellow")
            continue

        cprint(f"  Processing: {sheet_name} ({len(df)} rows)", "green")
        sheet_count = 0

        # Transform each row
        for idx, row in df.iterrows():
            record = transform_row(row, sheet_name, idx + 2)  # +2 for header + 0-index
            if record:
                all_records.append(record)
                sheet_count += 1

        sheet_stats[sheet_name] = sheet_count

    result_df = pd.DataFrame(all_records)
    cprint(f"\nTransformed {len(result_df)} records total", "green")

    # Delete existing CRIME_GUN_DB records and insert new
    cprint(f"\nSaving to database: {db_path}", "yellow")
    with sqlite3.connect(str(db_path)) as conn:
        # Delete existing
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM crime_gun_events WHERE source_dataset = 'CRIME_GUN_DB'"
        )
        existing_count = cursor.fetchone()[0]
        if existing_count > 0:
            cprint(f"  Deleting {existing_count} existing CRIME_GUN_DB records...", "yellow")
        cursor.execute("DELETE FROM crime_gun_events WHERE source_dataset = 'CRIME_GUN_DB'")

        # Insert new records
        result_df.to_sql("crime_gun_events", conn, if_exists="append", index=False)
        conn.commit()

    cprint(f"Saved {len(result_df)} records to database", "green")

    # Quality summary
    cprint("\n" + "=" * 60, "cyan")
    cprint("QUALITY SUMMARY", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")

    total = len(result_df)
    cprint(f"\n  Total records: {total}", "white")

    # Sheet breakdown
    cprint("\n  Records by sheet:", "white")
    for sheet, count in sheet_stats.items():
        cprint(f"    {sheet}: {count}", "white")

    # Jurisdiction coverage
    with_jurisdiction = result_df["jurisdiction_state"].notna().sum()
    cprint(
        f"\n  With jurisdiction: {with_jurisdiction} ({100*with_jurisdiction/total:.1f}%)",
        "white",
    )

    # Method breakdown
    cprint("\n  Jurisdiction method breakdown:", "white")
    method_counts = result_df["jurisdiction_method"].value_counts()
    for method, count in method_counts.items():
        cprint(f"    {method}: {count} ({100*count/total:.1f}%)", "white")

    # Trafficking flows
    with_flow = result_df["trafficking_origin"].notna().sum()
    cprint(f"\n  With trafficking flow: {with_flow}", "white")

    # Southwest border
    swb_count = result_df["is_southwest_border"].sum()
    cprint(f"  Southwest border trafficking: {swb_count}", "white")

    # Time to crime
    with_ttc = result_df["time_to_crime"].notna().sum()
    if with_ttc > 0:
        avg_ttc = result_df["time_to_crime"].dropna().mean()
        cprint(
            f"\n  With time-to-crime: {with_ttc} (avg: {avg_ttc:.0f} days)",
            "white",
        )

    # Boolean fields
    cprint("\n  FFL risk indicators:", "white")
    for col, label in [
        ("in_dl2_program", "In DL2 Program"),
        ("is_top_trace_ffl", "Top Trace FFL"),
        ("is_revoked", "Revoked"),
        ("is_charged_or_sued", "Charged/Sued"),
    ]:
        true_count = result_df[col].apply(lambda x: x is True).sum()
        cprint(f"    {label}: {true_count}", "white")

    cprint("\n" + "=" * 60, "cyan")
    cprint("ETL COMPLETE", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")

    return result_df


if __name__ == "__main__":
    main()
