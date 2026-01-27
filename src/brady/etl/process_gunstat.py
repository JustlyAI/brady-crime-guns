#!/usr/bin/env python3
"""
Brady ETL - Process Real DE Gunstat Data

Processes DE Gunstat Excel file and outputs normalized CSV.
"""

import pandas as pd
import re
from pathlib import Path
from termcolor import cprint


def get_project_root() -> Path:
    """Get project root directory"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / "src").exists():
            return parent
    return current.parent.parent.parent.parent


def parse_ffl_field(text):
    """Parse FFL field like 'Cabela's\nNewark, DE\nFFL 8-51-01809'"""
    if pd.isna(text):
        return {'dealer_name': None, 'dealer_city': None, 'dealer_state': None, 'dealer_ffl': None}

    text = str(text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    result = {'dealer_name': None, 'dealer_city': None, 'dealer_state': None, 'dealer_ffl': None}

    if len(lines) >= 1:
        result['dealer_name'] = lines[0]

    # Look for city, state pattern
    for line in lines[1:]:
        # Check for FFL number
        ffl_match = re.search(r'FFL\s*(\d+-\d+-\d+)', line, re.IGNORECASE)
        if ffl_match:
            result['dealer_ffl'] = ffl_match.group(1)
            continue

        # Check for City, ST pattern
        city_state = re.match(r'^([^,]+),\s*([A-Z]{2})$', line)
        if city_state:
            result['dealer_city'] = city_state.group(1)
            result['dealer_state'] = city_state.group(2)

    return result

def parse_case_field(text):
    """Parse case field like 'Jason Miles\nCase #:30-23-063056'"""
    if pd.isna(text):
        return {'defendant_name': None, 'case_number': None}

    text = str(text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    result = {'defendant_name': None, 'case_number': None}

    if len(lines) >= 1:
        result['defendant_name'] = lines[0]

    # Look for case number
    for line in lines:
        case_match = re.search(r'Case\s*[#:]?\s*:?\s*(\d+-\d+-\d+)', line, re.IGNORECASE)
        if case_match:
            result['case_number'] = case_match.group(1)
            break

    return result

def parse_firearm_field(text):
    """Parse firearm field like 'Taurus G2C #ABE573528\npurchased 7/2/20 by Bobby Cooks Jr'"""
    if pd.isna(text):
        return {'manufacturer': None, 'model': None, 'serial': None, 'caliber': None,
                'purchase_date': None, 'purchaser': None}

    text = str(text)
    result = {'manufacturer': None, 'model': None, 'serial': None, 'caliber': None,
              'purchase_date': None, 'purchaser': None}

    # Known manufacturers
    manufacturers = [
        'GLOCK', 'SMITH & WESSON', 'S&W', 'RUGER', 'TAURUS', 'FN', 'FNFIVESEVEN',
        'SIG SAUER', 'SIG', 'SPRINGFIELD', 'BERETTA', 'COLT', 'REMINGTON',
        'MOSSBERG', 'BROWNING', 'KIMBER', 'WALTHER', 'HI-POINT', 'HIPOINT',
        'KEL-TEC', 'KELTEC', 'SCCY', 'CANIK', 'HERITAGE', 'ROSSI', 'POLYMER80',
        'CENTURY', 'ANDERSON', 'PALMETTO', 'AERO', 'BUSHMASTER', 'DPMS',
        'ROCK RIVER', 'SEARS', 'CHARTER', 'NORTH AMERICAN', 'NAA', 'BRYCO',
        'JENNINGS', 'JIMENEZ', 'LORCIN', 'RAVEN', 'DAVIS', 'PHOENIX', 'COBRA'
    ]

    text_upper = text.upper()
    for mfr in manufacturers:
        if mfr in text_upper:
            result['manufacturer'] = mfr
            # Standardize some names
            if mfr in ['S&W']:
                result['manufacturer'] = 'SMITH & WESSON'
            if mfr in ['SIG']:
                result['manufacturer'] = 'SIG SAUER'
            if mfr in ['HIPOINT']:
                result['manufacturer'] = 'HI-POINT'
            if mfr in ['KELTEC']:
                result['manufacturer'] = 'KEL-TEC'
            break

    # Extract serial number (after #)
    serial_match = re.search(r'#\s*([A-Z0-9]+)', text, re.IGNORECASE)
    if serial_match:
        result['serial'] = serial_match.group(1)

    # Extract caliber
    caliber_patterns = [
        r'(9\s*mm)', r'(\.22)', r'(\.380)', r'(\.40)', r'(\.45)', r'(\.38)',
        r'(\.357)', r'(10\s*mm)', r'(5\.7)', r'(\.223)', r'(5\.56)', r'(7\.62)',
        r'(\.308)', r'(12\s*gauge)', r'(20\s*gauge)', r'(\.25)', r'(\.32)'
    ]
    for pattern in caliber_patterns:
        cal_match = re.search(pattern, text, re.IGNORECASE)
        if cal_match:
            result['caliber'] = cal_match.group(1).strip()
            break

    # Extract purchase date
    date_match = re.search(r'purchased?\s+(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
    if date_match:
        result['purchase_date'] = date_match.group(1)

    # Extract purchaser (after "by")
    purchaser_match = re.search(r'by\s+([A-Za-z\s]+?)(?:\s+\d|$)', text)
    if purchaser_match:
        result['purchaser'] = purchaser_match.group(1).strip()

    return result

def main(input_path: str = None, output_path: str = None):
    """
    Process DE Gunstat Excel file into normalized CSV.

    Args:
        input_path: Path to input Excel file (default: data/raw/DE_Gunstat_Final.xlsx)
        output_path: Path to output CSV file (default: data/processed/crime_gun_events.csv)
    """
    cprint("=" * 60, "cyan")
    cprint("PROCESSING REAL DE GUNSTAT DATA", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")

    # Resolve paths
    project_root = get_project_root()

    if input_path is None:
        xlsx_path = project_root / "data" / "raw" / "DE_Gunstat_Final.xlsx"
    else:
        xlsx_path = Path(input_path)

    if not xlsx_path.exists():
        cprint(f"ERROR: Input file not found: {xlsx_path}", "red")
        return None

    all_records = []

    # Process main sheet
    cprint(f"\nLoading: {xlsx_path}", "yellow")
    df = pd.read_excel(xlsx_path, sheet_name='all identified dealers')
    cprint(f"Loaded {len(df)} rows from 'all identified dealers'", "green")

    for idx, row in df.iterrows():
        # Parse FFL (column 0, named ' ')
        ffl_info = parse_ffl_field(row.iloc[0])

        # Parse Case (column 1)
        case_info = parse_case_field(row.get('Case'))

        # Parse Firearm info (column 3)
        firearm_info = parse_firearm_field(row.get('Firearm, purchase, NIBIN information'))

        # Get status
        status = row.get('Pending or resolved? ', None)
        if pd.notna(status):
            status = str(status).strip()

        # Get TTR (time to recovery)
        ttr = row.get('TTR ', None)
        ttr_category = row.get('TTR: over/under 3 years [1,095 days]\n* = when ttr over, but ttc to first nibin incident under 3 years', None)

        # Get NIBIN info
        has_nibin = row.get('NIBIN?', None)
        if pd.notna(has_nibin):
            has_nibin = str(has_nibin).upper() in ['YES', 'Y', 'TRUE', '1']
        else:
            has_nibin = False

        # Get trafficking indicia
        trafficking = row.get('Suspicious purchase circumstances/trafficking indicia?', None)
        has_trafficking_indicia = pd.notna(trafficking) and str(trafficking).strip() != ''

        # Get summary
        summary = row.get('Gunstat case summary ', None)

        # Determine interstate
        dealer_state = ffl_info['dealer_state']
        is_interstate = dealer_state is not None and dealer_state != 'DE'

        record = {
            'source_dataset': 'DE_GUNSTAT',
            'source_sheet': 'all identified dealers',
            'source_row': idx + 2,  # +2 for header and 0-index

            # Jurisdiction - all DE Gunstat is Delaware crimes
            'jurisdiction_state': 'DE',
            'jurisdiction_city': 'Wilmington',  # Default
            'jurisdiction_method': 'IMPLICIT',
            'jurisdiction_confidence': 'HIGH',

            # Dealer (Tier 3)
            'dealer_name': ffl_info['dealer_name'],
            'dealer_city': ffl_info['dealer_city'],
            'dealer_state': ffl_info['dealer_state'],
            'dealer_ffl': ffl_info['dealer_ffl'],

            # Manufacturer (Tier 1)
            'manufacturer_name': firearm_info['manufacturer'],

            # Firearm details
            'firearm_serial': firearm_info['serial'],
            'firearm_caliber': firearm_info['caliber'],

            # Case info
            'defendant_name': case_info['defendant_name'],
            'case_number': case_info['case_number'],
            'case_status': status,

            # Purchase info
            'purchase_date': firearm_info['purchase_date'],
            'purchaser_name': firearm_info['purchaser'],

            # Timing
            'time_to_recovery': ttr,
            'ttr_category': ttr_category,

            # Risk indicators
            'has_nibin': has_nibin,
            'has_trafficking_indicia': has_trafficking_indicia,
            'is_interstate': is_interstate,

            # Narrative
            'case_summary': summary
        }
        all_records.append(record)

    # Create DataFrame
    events_df = pd.DataFrame(all_records)

    # Save to CSV
    if output_path is None:
        output_dir = project_root / "data" / "processed"
        events_path = output_dir / "crime_gun_events.csv"
    else:
        events_path = Path(output_path)
        output_dir = events_path.parent

    output_dir.mkdir(parents=True, exist_ok=True)
    events_df.to_csv(events_path, index=False, encoding="utf-8")

    cprint(f"\nSaved {len(events_df)} records to {events_path}", "green")

    # Summary stats
    cprint("\n" + "=" * 60, "cyan")
    cprint("DATA SUMMARY", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")
    print(f"\nTotal Events: {len(events_df)}")
    print(f"\nTop Manufacturers:")
    print(events_df['manufacturer_name'].value_counts().head(10))
    print(f"\nTop Dealers:")
    print(events_df['dealer_name'].value_counts().head(10))
    print(f"\nDealer States:")
    print(events_df['dealer_state'].value_counts().head(10))
    print(f"\nInterstate Trafficking: {events_df['is_interstate'].sum()} ({events_df['is_interstate'].mean()*100:.1f}%)")
    print(f"\nCase Status:")
    print(events_df['case_status'].value_counts())

    cprint("\n✅ Data processing complete!", "green", attrs=["bold"])

    return events_df

if __name__ == '__main__':
    main()
