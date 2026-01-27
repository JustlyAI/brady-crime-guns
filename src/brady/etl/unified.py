"""
Brady Unified Gun Crime Database - Python ETL Scripts
======================================================

This module provides ETL (Extract, Transform, Load) functions to:
1. Create a unified schema for gun crime data
2. Import data from Crime Gun Dealer Database (Google Sheets)
3. Import data from Demand Letters spreadsheet (Google Sheets)
4. Import data from PA Gun Tracing Data (CSV and XLSX formats)

Requirements:
    pip install pandas openpyxl gspread google-auth google-auth-oauthlib

Setup:
    1. Enable Google Sheets API in Google Cloud Console
    2. Create credentials (OAuth 2.0 or Service Account)
    3. Download credentials JSON file
    4. Set GOOGLE_APPLICATION_CREDENTIALS environment variable

Author: Brady Gun Center ETL Pipeline
Date: 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import re
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Configuration for data source locations and IDs"""

    # Google Sheets IDs (from your Google Drive)
    CRIME_GUN_DB_ID = '1SOUl4Xrv6FLUY_t5bNAzO6xB8pftIYcfY3NUBwutC58'
    DEMAND_LETTERS_ID = '1l7iUG1t4sti3LM2HRVc2Yb3CZVBsh-GS0MiG5gITZLk'

    # Local file paths (update these to match your local file locations)
    PA_TRACE_CSV_PATH = 'PA-gunTracingData.csv'
    PA_TRACE_XLSX_PATH = 'PA-gunTracingData.xlsx'

    # Output paths
    OUTPUT_DIR = Path('./brady_unified_output')
    UNIFIED_DB_PATH = OUTPUT_DIR / 'brady_unified_database.xlsx'
    UNIFIED_CSV_PATH = OUTPUT_DIR / 'brady_unified_database.csv'


# =============================================================================
# UNIFIED SCHEMA DEFINITION
# =============================================================================

UNIFIED_SCHEMA = {
    # Record Identification
    'record_id': 'str',
    'source_system': 'str',
    'date_added': 'datetime64[ns]',

    # Dealer/FFL Information (Sale Jurisdiction - CRITICAL for nexus)
    'ffl_license_number': 'str',
    'ffl_license_name': 'str',
    'ffl_trade_name': 'str',
    'ffl_dealer_type': 'str',
    'ffl_premise_address': 'str',
    'ffl_premise_city': 'str',
    'ffl_premise_state': 'str',  # KEY JURISDICTION FIELD
    'ffl_premise_zip': 'str',
    'ffl_revoked_status': 'bool',
    'ffl_charged_sued_status': 'bool',
    'ffl_inspection_count': 'Int64',
    'ffl_top_trace_status': 'bool',

    # Manufacturer Information
    'manufacturer_name': 'str',
    'manufacturer_city': 'str',
    'manufacturer_state': 'str',
    'manufacturer_country': 'str',

    # Firearm Information
    'firearm_serial_number': 'str',
    'firearm_make': 'str',
    'firearm_model': 'str',
    'firearm_caliber': 'str',
    'firearm_type': 'str',
    'firearm_off_roster': 'bool',

    # Purchase/Sale Transaction
    'purchase_date': 'datetime64[ns]',
    'purchaser_name': 'str',
    'purchaser_city': 'str',
    'purchaser_state': 'str',
    'multiple_sale_indicator': 'bool',

    # Crime/Recovery Information (Harm Jurisdiction - CRITICAL for nexus)
    'recovery_date': 'datetime64[ns]',
    'recovery_city': 'str',
    'recovery_state': 'str',  # KEY JURISDICTION FIELD
    'recovery_zip': 'str',
    'recovery_county': 'str',
    'crime_type': 'str',
    'associated_crimes_description': 'str',
    'felon_possession': 'bool',
    'domestic_violence_indicator': 'bool',

    # Trafficking Flow Analysis (CRITICAL for nexus analysis)
    'source_state': 'str',       # Where gun was sold (same as ffl_premise_state)
    'destination_state': 'str',  # Where crime occurred (same as recovery_state)
    'trafficking_flow': 'str',   # Format: "XX-->YY" e.g., "PA-->NY"
    'is_interstate': 'bool',     # True if source != destination
    'is_international': 'bool',

    # Time to Crime Metrics (Key negligence indicator)
    'time_to_crime_days': 'Int64',
    'time_to_crime_category': 'str',  # Very Short, Short, Medium, Long
    'short_ttc_indicator': 'bool',    # True if < 3 years (1095 days)

    # Case/Litigation Information
    'case_name': 'str',
    'case_number': 'str',
    'case_court': 'str',
    'case_district': 'str',
    'case_type': 'str',
    'indictment_link': 'str',
    'trial_brief_link': 'str',

    # Brady Demand Letter 2 Program
    'in_dl2_program_2021': 'bool',
    'in_dl2_program_2022': 'bool',
    'in_dl2_program_2023': 'bool',
    'in_dl2_program_2024': 'bool',
    'dl2_letter_type_current': 'str',
    'dl2_most_recent_date': 'datetime64[ns]',
    'low_ttc_crime_count': 'Int64',
}

# Columns critical for jurisdiction nexus analysis (highlight these)
JURISDICTION_CRITICAL_COLUMNS = [
    'ffl_premise_state',
    'ffl_premise_city',
    'recovery_state',
    'recovery_city',
    'source_state',
    'destination_state',
    'trafficking_flow',
    'is_interstate',
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_empty_unified_df() -> pd.DataFrame:
    """Create an empty DataFrame with the unified schema"""
    df = pd.DataFrame(columns=list(UNIFIED_SCHEMA.keys()))
    return df


def normalize_state(state: str) -> str:
    """Normalize state names to 2-letter abbreviations"""
    if pd.isna(state) or not state:
        return ''

    state = str(state).strip().upper()

    # If already 2-letter abbreviation
    if len(state) == 2:
        return state

    # State name to abbreviation mapping
    state_map = {
        'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
        'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
        'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID',
        'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
        'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
        'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
        'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
        'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
        'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
        'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
        'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
        'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
        'WISCONSIN': 'WI', 'WYOMING': 'WY', 'DISTRICT OF COLUMBIA': 'DC',
        'PUERTO RICO': 'PR', 'GUAM': 'GU', 'VIRGIN ISLANDS': 'VI',
    }

    return state_map.get(state, state[:2] if len(state) >= 2 else state)


def categorize_ttc(days: int) -> str:
    """Categorize time-to-crime into risk categories"""
    if pd.isna(days) or days <= 0:
        return ''
    if days < 365:
        return 'Very Short (<1yr)'
    if days < 1095:  # 3 years
        return 'Short (<3yr)'
    if days < 1825:  # 5 years
        return 'Medium (3-5yr)'
    return 'Long (>5yr)'


def parse_ttc_value(ttc_str) -> Optional[int]:
    """Parse time-to-crime from various string formats"""
    if pd.isna(ttc_str):
        return None

    ttc_str = str(ttc_str).strip()

    # Try to extract number of days
    match = re.search(r'(\d+)\s*(?:days?)?', ttc_str, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Try direct conversion
    try:
        return int(float(ttc_str))
    except (ValueError, TypeError):
        return None


def parse_trafficking_flow(subject: str) -> Dict[str, str]:
    """Parse trafficking flow from case subject like 'Alaska --> California'"""
    result = {'flow': '', 'source_state': '', 'dest_state': ''}

    if pd.isna(subject) or not subject:
        return result

    subject = str(subject)

    # Match patterns like "Alaska --> California" or "AK->CA" or "AK to CA"
    match = re.search(r'([A-Za-z]{2,})\s*(?:-->|->|to|TO)\s*([A-Za-z]{2,})', subject, re.IGNORECASE)
    if match:
        result['source_state'] = normalize_state(match.group(1))
        result['dest_state'] = normalize_state(match.group(2))
        if result['source_state'] and result['dest_state']:
            result['flow'] = f"{result['source_state']}-->{result['dest_state']}"

    return result


def parse_case_citation(citation: str) -> Dict[str, str]:
    """Parse case citation for court and case info"""
    result = {'case_name': '', 'case_number': '', 'court': '', 'district': ''}

    if pd.isna(citation) or not citation:
        return result

    citation = str(citation)

    # Try to match "U.S. v. Smith, No. 23-cr-17 (D. Alaska)"
    match = re.match(r'([^,]+),?\s*(?:No\.\s*)?([\d\-\w]+)?\s*\(([^)]+)\)?', citation)
    if match:
        result['case_name'] = match.group(1).strip()
        result['case_number'] = match.group(2) or ''
        court_info = match.group(3) or ''
        result['court'] = court_info

        # Extract district
        dist_match = re.search(r'(D\.\s*\w+|[NSEW]\.D\.\s*\w+)', court_info)
        if dist_match:
            result['district'] = dist_match.group(0)
    else:
        result['case_name'] = citation[:100] if len(citation) > 100 else citation

    return result


def is_yes(value) -> bool:
    """Check if value represents a 'yes' response"""
    if pd.isna(value):
        return False
    v = str(value).lower().strip()
    return v in ('yes', 'true', '1', 'y', 'x')


def find_column(df: pd.DataFrame, *search_terms) -> Optional[str]:
    """Find a column matching any of the search terms (case-insensitive)"""
    for term in search_terms:
        term_lower = term.lower()
        for col in df.columns:
            if term_lower in str(col).lower():
                return col
    return None


# =============================================================================
# ETL: CRIME GUN DEALER DATABASE
# =============================================================================

def extract_crime_gun_db_from_excel(filepath: str) -> pd.DataFrame:
    """
    Extract data from Crime Gun Dealer Database Excel file.

    Expected sheets:
    - CG court doc FFLs
    - Philadelphia Trace
    - Rochester Trace
    """
    print(f"Reading Crime Gun Dealer Database from: {filepath}")

    all_records = []
    timestamp = datetime.now().strftime('%Y-%m-%d')

    try:
        # Read all sheets
        xl = pd.ExcelFile(filepath)

        for sheet_name in xl.sheet_names:
            print(f"  Processing sheet: {sheet_name}")
            df = pd.read_excel(xl, sheet_name=sheet_name)

            if df.empty:
                continue

            # Find relevant columns
            col_ffl = find_column(df, 'FFL', 'Dealer', 'License Name')
            col_address = find_column(df, 'Address', 'Premise Address')
            col_city = find_column(df, 'City', 'Premise City')
            col_state = find_column(df, 'State', 'Sta')
            col_license = find_column(df, 'license number', 'License #', 'FFL Number')
            col_top_trace = find_column(df, 'Top trace', 'Top Trace')
            col_revoked = find_column(df, 'Revoked')
            col_charged = find_column(df, 'charged', 'sued')
            col_case = find_column(df, 'Case')
            col_case_subject = find_column(df, 'Case subject', 'Subject')
            col_recovery_loc = find_column(df, 'Location', 'Recovery Location')
            col_recovery_info = find_column(df, 'Info on recoveries', 'Recovery Info')
            col_ttc = find_column(df, 'Time-to-recovery', 'Time to Crime', 'TTC')

            for idx, row in df.iterrows():
                # Skip empty rows
                ffl_name = row.get(col_ffl, '') if col_ffl else ''
                if pd.isna(ffl_name) or not str(ffl_name).strip():
                    continue

                # Parse case citation
                case_info = parse_case_citation(row.get(col_case, '') if col_case else '')

                # Parse trafficking flow
                flow_info = parse_trafficking_flow(row.get(col_case_subject, '') if col_case_subject else '')

                # Parse TTC
                ttc_days = parse_ttc_value(row.get(col_ttc, '') if col_ttc else '')

                # Get state info
                ffl_state = normalize_state(row.get(col_state, '') if col_state else '')

                record = {
                    'record_id': f'CG_{sheet_name[:3]}_{idx}',
                    'source_system': f'Crime_Gun_DB_{sheet_name}',
                    'date_added': timestamp,
                    'ffl_license_number': str(row.get(col_license, '')) if col_license else '',
                    'ffl_license_name': str(ffl_name),
                    'ffl_premise_address': str(row.get(col_address, '')) if col_address else '',
                    'ffl_premise_city': str(row.get(col_city, '')) if col_city else '',
                    'ffl_premise_state': ffl_state,
                    'ffl_top_trace_status': is_yes(row.get(col_top_trace, '')) if col_top_trace else False,
                    'ffl_revoked_status': is_yes(row.get(col_revoked, '')) if col_revoked else False,
                    'ffl_charged_sued_status': is_yes(row.get(col_charged, '')) if col_charged else False,
                    'case_name': case_info['case_name'],
                    'case_number': case_info['case_number'],
                    'case_court': case_info['court'],
                    'case_district': case_info['district'],
                    'source_state': ffl_state,
                    'destination_state': flow_info['dest_state'] or '',
                    'trafficking_flow': flow_info['flow'],
                    'is_interstate': ffl_state != flow_info['dest_state'] if flow_info['dest_state'] else False,
                    'time_to_crime_days': ttc_days,
                    'time_to_crime_category': categorize_ttc(ttc_days) if ttc_days else '',
                    'short_ttc_indicator': ttc_days is not None and ttc_days < 1095,
                    'associated_crimes_description': str(row.get(col_recovery_info, '')) if col_recovery_info else '',
                }
                all_records.append(record)

        print(f"  Extracted {len(all_records)} records from Crime Gun DB")
        return pd.DataFrame(all_records)

    except Exception as e:
        print(f"Error reading Crime Gun DB: {e}")
        return pd.DataFrame()


# =============================================================================
# ETL: DEMAND LETTERS DATABASE
# =============================================================================

def extract_demand_letters_from_excel(filepath: str) -> pd.DataFrame:
    """
    Extract data from Demand Letters 2 spreadsheet.

    Expected sheets:
    - Demand letter 2 FFLs
    - Full Data
    - Per State Analysis
    """
    print(f"Reading Demand Letters from: {filepath}")

    all_records = []
    timestamp = datetime.now().strftime('%Y-%m-%d')

    try:
        xl = pd.ExcelFile(filepath)

        # Find the main data sheet
        target_sheets = ['Full Data', 'Demand letter 2 FFLs', xl.sheet_names[0]]

        for sheet_name in target_sheets:
            if sheet_name not in xl.sheet_names:
                continue

            print(f"  Processing sheet: {sheet_name}")
            df = pd.read_excel(xl, sheet_name=sheet_name, header=None)

            if df.empty:
                continue

            # Handle potential multi-row headers
            # Check if row 1 looks like a continuation of headers
            headers = df.iloc[0].fillna('').astype(str).tolist()
            data_start_row = 1

            if len(df) > 1:
                row1 = df.iloc[1].fillna('').astype(str).tolist()
                if any('name' in str(v).lower() for v in row1[:5]):
                    # Combine header rows
                    headers = [f"{h} {r}".strip() for h, r in zip(headers, row1)]
                    data_start_row = 2

            df.columns = headers
            df = df.iloc[data_start_row:].reset_index(drop=True)

            # Find columns
            col_license_name = find_column(df, 'License Name', 'All License', 'Licensee')
            col_trade_name = find_column(df, 'Trade Name', 'All Trade', 'Business Name')
            col_address = find_column(df, 'Premise Address', 'Address')
            col_city = find_column(df, 'City', 'Premise City')
            col_state = find_column(df, 'State', 'Sta')
            col_zip = find_column(df, 'Zip', 'ZIP')
            col_dealer_type = find_column(df, 'Type of dealer', 'Dealer Type', 'Type')
            col_2021 = find_column(df, '2021')
            col_2022 = find_column(df, '2022')
            col_2023 = find_column(df, '2023')
            col_2024 = find_column(df, '2024')
            col_letter_type = find_column(df, 'Letter Type', 'DL2 Letter Type', 'Type of Letter')
            col_letter_date = find_column(df, 'DL2 Date', 'Letter Date', 'Date')

            for idx, row in df.iterrows():
                name = row.get(col_license_name, '') if col_license_name else ''
                if pd.isna(name) or not str(name).strip():
                    continue

                ffl_state = normalize_state(row.get(col_state, '') if col_state else '')

                record = {
                    'record_id': f'DL_{idx}',
                    'source_system': 'Demand_Letters_DB',
                    'date_added': timestamp,
                    'ffl_license_name': str(name),
                    'ffl_trade_name': str(row.get(col_trade_name, '')) if col_trade_name else '',
                    'ffl_premise_address': str(row.get(col_address, '')) if col_address else '',
                    'ffl_premise_city': str(row.get(col_city, '')) if col_city else '',
                    'ffl_premise_state': ffl_state,
                    'ffl_premise_zip': str(row.get(col_zip, '')) if col_zip else '',
                    'ffl_dealer_type': str(row.get(col_dealer_type, '')) if col_dealer_type else '',
                    'source_state': ffl_state,
                    'in_dl2_program_2021': is_yes(row.get(col_2021, '')) if col_2021 else False,
                    'in_dl2_program_2022': is_yes(row.get(col_2022, '')) if col_2022 else False,
                    'in_dl2_program_2023': is_yes(row.get(col_2023, '')) if col_2023 else False,
                    'in_dl2_program_2024': is_yes(row.get(col_2024, '')) if col_2024 else False,
                    'dl2_letter_type_current': str(row.get(col_letter_type, '')) if col_letter_type else '',
                }
                all_records.append(record)

            break  # Only process one sheet

        print(f"  Extracted {len(all_records)} records from Demand Letters")
        return pd.DataFrame(all_records)

    except Exception as e:
        print(f"Error reading Demand Letters: {e}")
        return pd.DataFrame()


# =============================================================================
# ETL: PA GUN TRACING DATA (CSV)
# =============================================================================

def extract_pa_trace_from_csv(filepath: str, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Extract data from PA Gun Tracing CSV file.
    This is ATF trace data with firearm recovery information.
    """
    print(f"Reading PA Trace CSV from: {filepath}")

    try:
        # Read CSV with chunking for large files
        if max_rows:
            df = pd.read_csv(filepath, nrows=max_rows, low_memory=False)
        else:
            df = pd.read_csv(filepath, low_memory=False)

        print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
        print(f"  Columns: {list(df.columns)[:15]}...")  # Print first 15 columns

        return _transform_pa_trace_data(df, 'PA_Trace_CSV')

    except Exception as e:
        print(f"Error reading PA Trace CSV: {e}")
        return pd.DataFrame()


def extract_pa_trace_from_xlsx(filepath: str, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Extract data from PA Gun Tracing XLSX file.
    This is ATF trace data with firearm recovery information.
    """
    print(f"Reading PA Trace XLSX from: {filepath}")

    try:
        # Read Excel file
        if max_rows:
            df = pd.read_excel(filepath, nrows=max_rows)
        else:
            df = pd.read_excel(filepath)

        print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
        print(f"  Columns: {list(df.columns)[:15]}...")

        return _transform_pa_trace_data(df, 'PA_Trace_XLSX')

    except Exception as e:
        print(f"Error reading PA Trace XLSX: {e}")
        return pd.DataFrame()


def _transform_pa_trace_data(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Transform PA trace data to unified schema"""

    all_records = []
    timestamp = datetime.now().strftime('%Y-%m-%d')

    # Find columns (ATF trace data has standardized column names)
    col_ffl_number = find_column(df, 'FFL_LICENSE', 'DEALER_FFL', 'FFL', 'LICENSE')
    col_ffl_name = find_column(df, 'DEALER_NAME', 'FFL_NAME', 'LICENSEE', 'NAME')
    col_ffl_city = find_column(df, 'DEALER_CITY', 'FFL_CITY', 'LICENSE_CITY')
    col_ffl_state = find_column(df, 'DEALER_STATE', 'FFL_STATE', 'LICENSE_STATE', 'PURCH_STATE')
    col_ffl_zip = find_column(df, 'DEALER_ZIP', 'FFL_ZIP')
    col_recovery_city = find_column(df, 'RECOVERY_CITY', 'REC_CITY', 'CRIME_CITY')
    col_recovery_state = find_column(df, 'RECOVERY_STATE', 'REC_STATE', 'CRIME_STATE')
    col_recovery_date = find_column(df, 'RECOVERY_DATE', 'REC_DATE')
    col_purchase_date = find_column(df, 'PURCHASE_DATE', 'SALE_DATE', 'PURCH_DATE')
    col_ttc = find_column(df, 'TIME_TO_CRIME', 'TTC', 'DAYS_TO_CRIME')
    col_make = find_column(df, 'MANUFACTURER', 'MAKE', 'MFG')
    col_model = find_column(df, 'MODEL')
    col_caliber = find_column(df, 'CALIBER', 'CAL')
    col_serial = find_column(df, 'SERIAL', 'SERIAL_NUMBER', 'SN')
    col_gun_type = find_column(df, 'GUN_TYPE', 'WEAPON_TYPE', 'TYPE')
    col_crime_type = find_column(df, 'CRIME_TYPE', 'OFFENSE', 'CRIME')

    print(f"  Column mapping:")
    print(f"    FFL Number: {col_ffl_number}")
    print(f"    FFL State: {col_ffl_state}")
    print(f"    Recovery State: {col_recovery_state}")
    print(f"    TTC: {col_ttc}")

    for idx, row in df.iterrows():
        # Get state information
        ffl_state = normalize_state(row.get(col_ffl_state, '') if col_ffl_state else '')
        recovery_state = normalize_state(row.get(col_recovery_state, '') if col_recovery_state else '')

        # Parse TTC
        ttc_days = parse_ttc_value(row.get(col_ttc, '') if col_ttc else '')

        # Build trafficking flow
        trafficking_flow = ''
        if ffl_state and recovery_state:
            trafficking_flow = f"{ffl_state}-->{recovery_state}"

        is_interstate = bool(ffl_state and recovery_state and ffl_state != recovery_state)

        record = {
            'record_id': f'{source_name}_{idx}',
            'source_system': source_name,
            'date_added': timestamp,
            'ffl_license_number': str(row.get(col_ffl_number, '')) if col_ffl_number else '',
            'ffl_license_name': str(row.get(col_ffl_name, '')) if col_ffl_name else '',
            'ffl_premise_city': str(row.get(col_ffl_city, '')) if col_ffl_city else '',
            'ffl_premise_state': ffl_state,
            'ffl_premise_zip': str(row.get(col_ffl_zip, '')) if col_ffl_zip else '',
            'firearm_serial_number': str(row.get(col_serial, '')) if col_serial else '',
            'firearm_make': str(row.get(col_make, '')) if col_make else '',
            'firearm_model': str(row.get(col_model, '')) if col_model else '',
            'firearm_caliber': str(row.get(col_caliber, '')) if col_caliber else '',
            'firearm_type': str(row.get(col_gun_type, '')) if col_gun_type else '',
            'purchase_date': row.get(col_purchase_date, '') if col_purchase_date else '',
            'recovery_date': row.get(col_recovery_date, '') if col_recovery_date else '',
            'recovery_city': str(row.get(col_recovery_city, '')) if col_recovery_city else '',
            'recovery_state': recovery_state,
            'crime_type': str(row.get(col_crime_type, '')) if col_crime_type else '',
            'source_state': ffl_state,
            'destination_state': recovery_state,
            'trafficking_flow': trafficking_flow,
            'is_interstate': is_interstate,
            'time_to_crime_days': ttc_days,
            'time_to_crime_category': categorize_ttc(ttc_days) if ttc_days else '',
            'short_ttc_indicator': ttc_days is not None and ttc_days < 1095,
        }
        all_records.append(record)

        # Progress indicator for large files
        if (idx + 1) % 100000 == 0:
            print(f"    Processed {idx + 1} rows...")

    print(f"  Transformed {len(all_records)} records from PA Trace")
    return pd.DataFrame(all_records)


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def create_jurisdiction_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary of jurisdiction nexus opportunities.
    Analyzes where crimes occur vs where guns were sold.
    """
    if df.empty:
        return pd.DataFrame()

    # Group by destination state (where harm occurred)
    summary_data = []

    for dest_state in df['destination_state'].dropna().unique():
        if not dest_state:
            continue

        state_df = df[df['destination_state'] == dest_state]

        total_crimes = len(state_df)
        interstate_count = state_df['is_interstate'].sum()
        short_ttc_count = state_df['short_ttc_indicator'].sum()

        # Find top source states
        source_counts = state_df[state_df['source_state'] != dest_state]['source_state'].value_counts()
        top_source = f"{source_counts.index[0]} ({source_counts.iloc[0]})" if len(source_counts) > 0 else ''

        # Calculate nexus score (higher = stronger case for nuisance action)
        # Weight: total crimes + 2x interstate + 3x short TTC
        nexus_score = total_crimes + (interstate_count * 2) + (short_ttc_count * 3)

        summary_data.append({
            'destination_state': dest_state,
            'total_crime_guns': total_crimes,
            'interstate_trafficked': interstate_count,
            'short_ttc_count': short_ttc_count,
            'top_source_state': top_source,
            'nexus_score': nexus_score,
        })

    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.sort_values('nexus_score', ascending=False)

    return summary_df


def create_dealer_risk_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a risk summary for individual dealers.
    Identifies high-risk FFLs based on crime gun traces.
    """
    if df.empty:
        return pd.DataFrame()

    # Group by dealer
    dealer_summary = df.groupby(['ffl_license_name', 'ffl_premise_state']).agg({
        'record_id': 'count',
        'is_interstate': 'sum',
        'short_ttc_indicator': 'sum',
        'time_to_crime_days': 'mean',
        'in_dl2_program_2021': 'max',
        'in_dl2_program_2022': 'max',
        'in_dl2_program_2023': 'max',
        'in_dl2_program_2024': 'max',
        'ffl_revoked_status': 'max',
        'ffl_charged_sued_status': 'max',
    }).reset_index()

    dealer_summary.columns = [
        'dealer_name', 'dealer_state', 'total_crime_guns', 'interstate_count',
        'short_ttc_count', 'avg_ttc_days', 'dl2_2021', 'dl2_2022', 'dl2_2023', 'dl2_2024',
        'revoked', 'charged_sued'
    ]

    # Calculate risk score
    dealer_summary['risk_score'] = (
        dealer_summary['total_crime_guns'] +
        (dealer_summary['interstate_count'] * 2) +
        (dealer_summary['short_ttc_count'] * 3) +
        (dealer_summary['dl2_2024'].fillna(False).astype(int) * 10) +
        (dealer_summary['revoked'].fillna(False).astype(int) * 20) +
        (dealer_summary['charged_sued'].fillna(False).astype(int) * 15)
    )

    return dealer_summary.sort_values('risk_score', ascending=False)


# =============================================================================
# MAIN ETL PIPELINE
# =============================================================================

def run_full_etl(
    crime_gun_path: Optional[str] = None,
    demand_letters_path: Optional[str] = None,
    pa_trace_csv_path: Optional[str] = None,
    pa_trace_xlsx_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    max_pa_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Run the complete ETL pipeline to create a unified database.

    Args:
        crime_gun_path: Path to Crime Gun Dealer DB Excel file
        demand_letters_path: Path to Demand Letters Excel file
        pa_trace_csv_path: Path to PA Trace CSV file
        pa_trace_xlsx_path: Path to PA Trace XLSX file
        output_dir: Directory to save output files
        max_pa_rows: Limit PA trace rows (for testing)

    Returns:
        Combined DataFrame with unified schema
    """
    print("=" * 60)
    print("BRADY UNIFIED GUN CRIME DATABASE - ETL PIPELINE")
    print("=" * 60)
    print()

    # Setup output directory
    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = Config.OUTPUT_DIR
    out_path.mkdir(parents=True, exist_ok=True)

    all_dataframes = []

    # 1. Process Crime Gun Dealer DB
    if crime_gun_path and Path(crime_gun_path).exists():
        print("\n[1/4] Processing Crime Gun Dealer Database...")
        crime_gun_df = extract_crime_gun_db_from_excel(crime_gun_path)
        if not crime_gun_df.empty:
            all_dataframes.append(crime_gun_df)
    else:
        print("\n[1/4] Skipping Crime Gun DB (file not found)")

    # 2. Process Demand Letters
    if demand_letters_path and Path(demand_letters_path).exists():
        print("\n[2/4] Processing Demand Letters Database...")
        demand_letters_df = extract_demand_letters_from_excel(demand_letters_path)
        if not demand_letters_df.empty:
            all_dataframes.append(demand_letters_df)
    else:
        print("\n[2/4] Skipping Demand Letters (file not found)")

    # 3. Process PA Trace CSV
    if pa_trace_csv_path and Path(pa_trace_csv_path).exists():
        print("\n[3/4] Processing PA Trace CSV...")
        pa_csv_df = extract_pa_trace_from_csv(pa_trace_csv_path, max_rows=max_pa_rows)
        if not pa_csv_df.empty:
            all_dataframes.append(pa_csv_df)
    else:
        print("\n[3/4] Skipping PA Trace CSV (file not found)")

    # 4. Process PA Trace XLSX
    if pa_trace_xlsx_path and Path(pa_trace_xlsx_path).exists():
        print("\n[4/4] Processing PA Trace XLSX...")
        pa_xlsx_df = extract_pa_trace_from_xlsx(pa_trace_xlsx_path, max_rows=max_pa_rows)
        if not pa_xlsx_df.empty:
            all_dataframes.append(pa_xlsx_df)
    else:
        print("\n[4/4] Skipping PA Trace XLSX (file not found)")

    # Combine all data
    print("\n" + "=" * 60)
    print("COMBINING DATA...")

    if not all_dataframes:
        print("WARNING: No data was extracted from any source!")
        return pd.DataFrame()

    unified_df = pd.concat(all_dataframes, ignore_index=True)

    # Ensure all columns from schema exist
    for col in UNIFIED_SCHEMA.keys():
        if col not in unified_df.columns:
            unified_df[col] = None

    # Reorder columns to match schema
    unified_df = unified_df[list(UNIFIED_SCHEMA.keys())]

    print(f"\nTotal records in unified database: {len(unified_df)}")
    print(f"Columns: {len(unified_df.columns)}")

    # Generate summaries
    print("\n" + "=" * 60)
    print("GENERATING ANALYSIS SUMMARIES...")

    jurisdiction_summary = create_jurisdiction_summary(unified_df)
    dealer_summary = create_dealer_risk_summary(unified_df)

    # Save outputs
    print("\n" + "=" * 60)
    print("SAVING OUTPUT FILES...")

    # Save main unified database
    unified_xlsx_path = out_path / 'brady_unified_database.xlsx'
    unified_csv_path = out_path / 'brady_unified_database.csv'

    # Save to Excel with multiple sheets
    with pd.ExcelWriter(unified_xlsx_path, engine='openpyxl') as writer:
        unified_df.to_excel(writer, sheet_name='Unified_Data', index=False)
        jurisdiction_summary.to_excel(writer, sheet_name='Jurisdiction_Summary', index=False)
        dealer_summary.to_excel(writer, sheet_name='Dealer_Risk_Summary', index=False)

    # Save CSV version
    unified_df.to_csv(unified_csv_path, index=False)

    print(f"\nOutput files saved to: {out_path}")
    print(f"  - {unified_xlsx_path.name}")
    print(f"  - {unified_csv_path.name}")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"\nTotal Records: {len(unified_df)}")
    print(f"\nRecords by Source:")
    print(unified_df['source_system'].value_counts().to_string())
    print(f"\nInterstate Trafficking: {unified_df['is_interstate'].sum()} records")
    print(f"Short TTC (<3yr): {unified_df['short_ttc_indicator'].sum()} records")
    print(f"\nTop 10 Destination States (harm locations):")
    print(unified_df['destination_state'].value_counts().head(10).to_string())

    return unified_df


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Brady Unified Gun Crime Database ETL Pipeline'
    )
    parser.add_argument('--crime-gun', type=str, help='Path to Crime Gun Dealer DB Excel file')
    parser.add_argument('--demand-letters', type=str, help='Path to Demand Letters Excel file')
    parser.add_argument('--pa-trace-csv', type=str, help='Path to PA Trace CSV file')
    parser.add_argument('--pa-trace-xlsx', type=str, help='Path to PA Trace XLSX file')
    parser.add_argument('--output-dir', type=str, default='./brady_unified_output', help='Output directory')
    parser.add_argument('--max-rows', type=int, help='Limit PA trace rows (for testing)')

    args = parser.parse_args()

    # Run ETL
    result_df = run_full_etl(
        crime_gun_path=args.crime_gun,
        demand_letters_path=args.demand_letters,
        pa_trace_csv_path=args.pa_trace_csv,
        pa_trace_xlsx_path=args.pa_trace_xlsx,
        output_dir=args.output_dir,
        max_pa_rows=args.max_rows,
    )

    print("\n" + "=" * 60)
    print("ETL PIPELINE COMPLETE")
    print("=" * 60)
