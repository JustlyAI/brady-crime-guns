"""
Brady Gun Crime Database - Relational ETL Pipeline
===================================================

This script creates a RELATIONAL database structure instead of one flat table.

Structure:
    1. dim_dealers      - Master list of unique FFLs (join key for everything)
    2. fact_dl2         - Demand Letter 2 program participation
    3. fact_cases       - Crime gun court cases
    4. fact_traces      - Individual firearm traces (PA data)

This approach enables queries like:
    - "Show all traces for dealers in the DL2 program"
    - "Which DL2 dealers have short time-to-crime patterns?"
    - "Aggregate trace counts by dealer and compare to DL2 status"

Author: Brady Gun Center ETL Pipeline
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict
import re
import hashlib


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    OUTPUT_DIR = Path('./brady_relational_output')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_dealer_name(name: str) -> str:
    """Normalize dealer name for matching across datasets"""
    if pd.isna(name) or not name:
        return ''

    name = str(name).upper().strip()

    # Remove common suffixes
    for suffix in [' LLC', ' INC', ' CORP', ' LLP', ' CO', ' COMPANY', '.', ',']:
        name = name.replace(suffix, '')

    # Remove extra whitespace
    name = ' '.join(name.split())

    return name


def normalize_state(state: str) -> str:
    """Normalize state to 2-letter code"""
    if pd.isna(state) or not state:
        return ''

    state = str(state).strip().upper()

    if len(state) == 2:
        return state

    state_map = {
        'PENNSYLVANIA': 'PA', 'CALIFORNIA': 'CA', 'NEW YORK': 'NY',
        'TEXAS': 'TX', 'FLORIDA': 'FL', 'OHIO': 'OH', 'GEORGIA': 'GA',
        'VIRGINIA': 'VA', 'NORTH CAROLINA': 'NC', 'ARIZONA': 'AZ',
        'ALASKA': 'AK', 'ALABAMA': 'AL', 'ARKANSAS': 'AR', 'COLORADO': 'CO',
        'CONNECTICUT': 'CT', 'DELAWARE': 'DE', 'HAWAII': 'HI', 'IDAHO': 'ID',
        'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
        'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
        'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN',
        'MISSISSIPPI': 'MS', 'MISSOURI': 'MO', 'MONTANA': 'MT',
        'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH',
        'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NORTH DAKOTA': 'ND',
        'OKLAHOMA': 'OK', 'OREGON': 'OR', 'RHODE ISLAND': 'RI',
        'SOUTH CAROLINA': 'SC', 'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN',
        'UTAH': 'UT', 'VERMONT': 'VT', 'WASHINGTON': 'WA',
        'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY',
        'DISTRICT OF COLUMBIA': 'DC',
    }

    return state_map.get(state, state[:2] if len(state) >= 2 else '')


def create_dealer_id(name: str, state: str) -> str:
    """Create a consistent dealer ID from name + state"""
    normalized = f"{normalize_dealer_name(name)}|{normalize_state(state)}"
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def find_column(df: pd.DataFrame, *search_terms) -> Optional[str]:
    """Find column matching search terms"""
    for term in search_terms:
        term_lower = term.lower()
        for col in df.columns:
            if term_lower in str(col).lower():
                return col
    return None


def parse_ttc(value) -> Optional[int]:
    """Parse time-to-crime value"""
    if pd.isna(value):
        return None
    try:
        return int(float(str(value).replace(',', '')))
    except:
        match = re.search(r'(\d+)', str(value))
        return int(match.group(1)) if match else None


# =============================================================================
# EXTRACT FUNCTIONS
# =============================================================================

def extract_demand_letters(filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract Demand Letters data into:
    - dealers: unique dealer info
    - dl2_facts: program participation facts
    """
    print(f"Reading Demand Letters from: {filepath}")

    xl = pd.ExcelFile(filepath)

    # Find the main data sheet
    for sheet_name in ['Full Data', 'Demand letter 2 FFLs']:
        if sheet_name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet_name, header=[0, 1])
            break
    else:
        df = pd.read_excel(xl, sheet_name=xl.sheet_names[0], header=[0, 1])

    # Flatten multi-level headers
    df.columns = [' '.join(str(c) for c in col).strip() for col in df.columns]

    print(f"  Columns: {list(df.columns)[:10]}...")

    # Find relevant columns
    col_license = find_column(df, 'License Name')
    col_trade = find_column(df, 'Trade Name')
    col_state = find_column(df, 'Sta', 'State')
    col_city = find_column(df, 'City')
    col_address = find_column(df, 'Address', 'Premise')
    col_2021 = find_column(df, '2021')
    col_2022 = find_column(df, '2022')
    col_2023 = find_column(df, '2023')
    col_2024 = find_column(df, '2024')
    col_letter_type_2023 = find_column(df, 'Type of Letter in 2023', 'Letter in 2023')
    col_letter_type_2022 = find_column(df, 'Type of Letter in 2022', 'Letter in 2022')

    dealers = []
    dl2_facts = []

    for idx, row in df.iterrows():
        license_name = row.get(col_license, '') if col_license else ''
        if pd.isna(license_name) or not str(license_name).strip():
            continue

        state = normalize_state(row.get(col_state, '') if col_state else '')
        dealer_id = create_dealer_id(license_name, state)

        # Dealer dimension record
        dealers.append({
            'dealer_id': dealer_id,
            'license_name': str(license_name).strip(),
            'trade_name': str(row.get(col_trade, '')).strip() if col_trade else '',
            'state': state,
            'city': str(row.get(col_city, '')).strip() if col_city else '',
            'address': str(row.get(col_address, '')).strip() if col_address else '',
            'source': 'demand_letters',
        })

        # DL2 participation facts (one row per year)
        for year, col in [(2021, col_2021), (2022, col_2022), (2023, col_2023), (2024, col_2024)]:
            if col:
                in_program = str(row.get(col, '')).lower().strip() in ('yes', 'y', 'true', '1')
                if in_program:
                    letter_type = ''
                    if year == 2023 and col_letter_type_2023:
                        letter_type = str(row.get(col_letter_type_2023, ''))
                    elif year == 2022 and col_letter_type_2022:
                        letter_type = str(row.get(col_letter_type_2022, ''))

                    dl2_facts.append({
                        'dealer_id': dealer_id,
                        'year': year,
                        'in_program': True,
                        'letter_type': letter_type if not pd.isna(letter_type) else '',
                    })

    print(f"  Extracted {len(dealers)} dealers, {len(dl2_facts)} DL2 participation records")

    return pd.DataFrame(dealers), pd.DataFrame(dl2_facts)


def extract_crime_gun_db(filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract Crime Gun DB into:
    - dealers: unique dealer info
    - case_facts: court case information
    """
    print(f"Reading Crime Gun DB from: {filepath}")

    xl = pd.ExcelFile(filepath)

    dealers = []
    case_facts = []

    for sheet_name in xl.sheet_names:
        print(f"  Processing sheet: {sheet_name}")
        df = pd.read_excel(xl, sheet_name=sheet_name)

        if df.empty:
            continue

        col_ffl = find_column(df, 'FFL')
        col_address = find_column(df, 'Address')
        col_city = find_column(df, 'City')
        col_state = find_column(df, 'State')
        col_license = find_column(df, 'license number')
        col_case = find_column(df, 'Case')
        col_case_subject = find_column(df, 'Case subject')
        col_revoked = find_column(df, 'Revoked')
        col_charged = find_column(df, 'charged')
        col_top_trace = find_column(df, 'Top trace')

        for idx, row in df.iterrows():
            ffl_name = row.get(col_ffl, '') if col_ffl else ''
            if pd.isna(ffl_name) or not str(ffl_name).strip():
                continue

            state = normalize_state(row.get(col_state, '') if col_state else '')
            dealer_id = create_dealer_id(ffl_name, state)

            # Dealer record
            dealers.append({
                'dealer_id': dealer_id,
                'license_name': str(ffl_name).strip(),
                'trade_name': '',
                'state': state,
                'city': str(row.get(col_city, '')).strip() if col_city else '',
                'address': str(row.get(col_address, '')).strip() if col_address else '',
                'license_number': str(row.get(col_license, '')) if col_license else '',
                'is_revoked': str(row.get(col_revoked, '')).lower() in ('yes', 'y', 'true') if col_revoked else False,
                'is_charged': str(row.get(col_charged, '')).lower() in ('yes', 'y', 'true') if col_charged else False,
                'is_top_trace': str(row.get(col_top_trace, '')).lower() in ('yes', 'y', 'true') if col_top_trace else False,
                'source': f'crime_gun_db_{sheet_name}',
            })

            # Case fact record
            case_name = str(row.get(col_case, '')) if col_case else ''
            case_subject = str(row.get(col_case_subject, '')) if col_case_subject else ''

            if case_name or case_subject:
                case_facts.append({
                    'dealer_id': dealer_id,
                    'case_name': case_name if not pd.isna(case_name) else '',
                    'case_subject': case_subject if not pd.isna(case_subject) else '',
                    'source_sheet': sheet_name,
                })

    print(f"  Extracted {len(dealers)} dealers, {len(case_facts)} case records")

    return pd.DataFrame(dealers), pd.DataFrame(case_facts)


def extract_pa_traces(filepath: str, file_type: str = 'csv', max_rows: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract PA Trace data into:
    - dealers: unique dealer info (extracted from trace data)
    - trace_facts: individual firearm traces
    """
    print(f"Reading PA Traces from: {filepath} ({file_type})")

    if file_type == 'csv':
        df = pd.read_csv(filepath, nrows=max_rows, low_memory=False)
    else:
        df = pd.read_excel(filepath, nrows=max_rows)

    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)[:15]}...")

    # Find columns
    col_ffl_name = find_column(df, 'DEALER_NAME', 'FFL_NAME', 'LICENSEE', 'NAME')
    col_ffl_state = find_column(df, 'DEALER_STATE', 'FFL_STATE', 'PURCH_STATE')
    col_ffl_city = find_column(df, 'DEALER_CITY', 'FFL_CITY')
    col_ffl_number = find_column(df, 'FFL_LICENSE', 'DEALER_FFL', 'FFL', 'LICENSE')
    col_recovery_state = find_column(df, 'RECOVERY_STATE', 'REC_STATE')
    col_recovery_city = find_column(df, 'RECOVERY_CITY', 'REC_CITY')
    col_recovery_date = find_column(df, 'RECOVERY_DATE', 'REC_DATE')
    col_purchase_date = find_column(df, 'PURCHASE_DATE', 'SALE_DATE')
    col_ttc = find_column(df, 'TIME_TO_CRIME', 'TTC')
    col_serial = find_column(df, 'SERIAL')
    col_make = find_column(df, 'MANUFACTURER', 'MAKE')
    col_model = find_column(df, 'MODEL')
    col_caliber = find_column(df, 'CALIBER', 'CAL')
    col_type = find_column(df, 'GUN_TYPE', 'WEAPON_TYPE', 'TYPE')

    print(f"  Key column mapping:")
    print(f"    Dealer Name: {col_ffl_name}")
    print(f"    Dealer State: {col_ffl_state}")
    print(f"    Recovery State: {col_recovery_state}")
    print(f"    TTC: {col_ttc}")

    dealers_dict = {}  # Use dict to dedupe
    trace_facts = []

    for idx, row in df.iterrows():
        ffl_name = str(row.get(col_ffl_name, '')).strip() if col_ffl_name else ''
        ffl_state = normalize_state(row.get(col_ffl_state, '') if col_ffl_state else '')

        if not ffl_name:
            continue

        dealer_id = create_dealer_id(ffl_name, ffl_state)

        # Add to dealers dict (dedupes automatically)
        if dealer_id not in dealers_dict:
            dealers_dict[dealer_id] = {
                'dealer_id': dealer_id,
                'license_name': ffl_name,
                'trade_name': '',
                'state': ffl_state,
                'city': str(row.get(col_ffl_city, '')).strip() if col_ffl_city else '',
                'license_number': str(row.get(col_ffl_number, '')) if col_ffl_number else '',
                'source': 'pa_traces',
            }

        # Trace fact record
        recovery_state = normalize_state(row.get(col_recovery_state, '') if col_recovery_state else '')
        ttc = parse_ttc(row.get(col_ttc, '') if col_ttc else '')

        trace_facts.append({
            'trace_id': f"PA_{idx}",
            'dealer_id': dealer_id,
            'recovery_state': recovery_state,
            'recovery_city': str(row.get(col_recovery_city, '')).strip() if col_recovery_city else '',
            'recovery_date': row.get(col_recovery_date, '') if col_recovery_date else '',
            'purchase_date': row.get(col_purchase_date, '') if col_purchase_date else '',
            'time_to_crime_days': ttc,
            'is_short_ttc': ttc is not None and ttc < 1095,
            'is_interstate': ffl_state != recovery_state and ffl_state and recovery_state,
            'trafficking_flow': f"{ffl_state}-->{recovery_state}" if ffl_state and recovery_state else '',
            'firearm_serial': str(row.get(col_serial, '')) if col_serial else '',
            'firearm_make': str(row.get(col_make, '')) if col_make else '',
            'firearm_model': str(row.get(col_model, '')) if col_model else '',
            'firearm_caliber': str(row.get(col_caliber, '')) if col_caliber else '',
            'firearm_type': str(row.get(col_type, '')) if col_type else '',
        })

        if (idx + 1) % 100000 == 0:
            print(f"    Processed {idx + 1} rows...")

    dealers = pd.DataFrame(list(dealers_dict.values()))
    traces = pd.DataFrame(trace_facts)

    print(f"  Extracted {len(dealers)} unique dealers, {len(traces)} trace records")

    return dealers, traces


# =============================================================================
# MERGE & DEDUPE DEALERS
# =============================================================================

def create_dealer_dimension(dealer_dfs: list) -> pd.DataFrame:
    """
    Merge dealer records from all sources into one dimension table.
    Prioritize data from sources with more complete info.
    """
    print("\nCreating unified dealer dimension...")

    all_dealers = pd.concat(dealer_dfs, ignore_index=True)
    print(f"  Total dealer records before dedup: {len(all_dealers)}")

    # Group by dealer_id and take best values
    def merge_dealer_records(group):
        """Merge multiple records for same dealer"""
        result = {
            'dealer_id': group['dealer_id'].iloc[0],
            'license_name': group['license_name'].iloc[0],
            'trade_name': group['trade_name'].dropna().iloc[0] if group['trade_name'].dropna().any() else '',
            'state': group['state'].iloc[0],
            'city': group['city'].dropna().iloc[0] if group['city'].dropna().any() else '',
            'address': group['address'].dropna().iloc[0] if 'address' in group.columns and group['address'].dropna().any() else '',
            'license_number': group['license_number'].dropna().iloc[0] if 'license_number' in group.columns and group['license_number'].dropna().any() else '',
            'is_revoked': group['is_revoked'].any() if 'is_revoked' in group.columns else False,
            'is_charged': group['is_charged'].any() if 'is_charged' in group.columns else False,
            'is_top_trace': group['is_top_trace'].any() if 'is_top_trace' in group.columns else False,
            'sources': ','.join(group['source'].unique()),
        }
        return pd.Series(result)

    dim_dealers = all_dealers.groupby('dealer_id').apply(merge_dealer_records).reset_index(drop=True)

    print(f"  Unique dealers after dedup: {len(dim_dealers)}")

    return dim_dealers


# =============================================================================
# ANALYSIS VIEWS
# =============================================================================

def create_dealer_summary(dim_dealers: pd.DataFrame,
                          fact_dl2: pd.DataFrame,
                          fact_traces: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary view joining dealers with their DL2 status and trace counts.
    This is the analysis-ready table for jurisdiction nexus work.
    """
    print("\nCreating dealer summary view...")

    # Start with dealers
    summary = dim_dealers.copy()

    # Add DL2 program status
    if not fact_dl2.empty:
        dl2_summary = fact_dl2.groupby('dealer_id').agg({
            'year': lambda x: list(x),
            'in_program': 'sum',
        }).reset_index()
        dl2_summary.columns = ['dealer_id', 'dl2_years', 'dl2_years_count']
        dl2_summary['in_dl2_program'] = True

        summary = summary.merge(dl2_summary, on='dealer_id', how='left')
        summary['in_dl2_program'] = summary['in_dl2_program'].fillna(False)
    else:
        summary['in_dl2_program'] = False
        summary['dl2_years'] = None
        summary['dl2_years_count'] = 0

    # Add trace statistics
    if not fact_traces.empty:
        trace_summary = fact_traces.groupby('dealer_id').agg({
            'trace_id': 'count',
            'is_short_ttc': 'sum',
            'is_interstate': 'sum',
            'time_to_crime_days': 'mean',
        }).reset_index()
        trace_summary.columns = ['dealer_id', 'total_traces', 'short_ttc_count',
                                  'interstate_count', 'avg_ttc_days']

        summary = summary.merge(trace_summary, on='dealer_id', how='left')
        summary['total_traces'] = summary['total_traces'].fillna(0).astype(int)
        summary['short_ttc_count'] = summary['short_ttc_count'].fillna(0).astype(int)
        summary['interstate_count'] = summary['interstate_count'].fillna(0).astype(int)
    else:
        summary['total_traces'] = 0
        summary['short_ttc_count'] = 0
        summary['interstate_count'] = 0
        summary['avg_ttc_days'] = None

    # Calculate risk score
    summary['risk_score'] = (
        summary['total_traces'] +
        summary['short_ttc_count'] * 3 +
        summary['interstate_count'] * 2 +
        summary['in_dl2_program'].astype(int) * 10 +
        summary['is_revoked'].astype(int) * 20 +
        summary['is_charged'].astype(int) * 15
    )

    summary = summary.sort_values('risk_score', ascending=False)

    print(f"  Created summary for {len(summary)} dealers")

    return summary


def create_jurisdiction_analysis(fact_traces: pd.DataFrame,
                                 dim_dealers: pd.DataFrame) -> pd.DataFrame:
    """
    Create jurisdiction nexus analysis showing trafficking patterns.
    """
    print("\nCreating jurisdiction analysis...")

    if fact_traces.empty:
        return pd.DataFrame()

    # Join traces with dealer info
    traces_with_dealers = fact_traces.merge(
        dim_dealers[['dealer_id', 'state', 'license_name']],
        on='dealer_id',
        how='left',
        suffixes=('', '_dealer')
    )

    # Group by destination state (where harm occurred)
    jurisdiction_stats = traces_with_dealers.groupby('recovery_state').agg({
        'trace_id': 'count',
        'is_interstate': 'sum',
        'is_short_ttc': 'sum',
        'state': lambda x: x.value_counts().head(3).to_dict(),  # Top source states
    }).reset_index()

    jurisdiction_stats.columns = ['destination_state', 'total_traces',
                                   'interstate_count', 'short_ttc_count', 'top_source_states']

    # Calculate nexus score
    jurisdiction_stats['nexus_score'] = (
        jurisdiction_stats['total_traces'] +
        jurisdiction_stats['interstate_count'] * 2 +
        jurisdiction_stats['short_ttc_count'] * 3
    )

    jurisdiction_stats = jurisdiction_stats.sort_values('nexus_score', ascending=False)

    print(f"  Analyzed {len(jurisdiction_stats)} destination states")

    return jurisdiction_stats


# =============================================================================
# MAIN ETL PIPELINE
# =============================================================================

def run_relational_etl(
    demand_letters_path: Optional[str] = None,
    crime_gun_path: Optional[str] = None,
    pa_trace_csv_path: Optional[str] = None,
    pa_trace_xlsx_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    max_trace_rows: Optional[int] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Run the relational ETL pipeline.

    Returns dict of DataFrames:
        - dim_dealers: Dealer dimension table
        - fact_dl2: DL2 program participation
        - fact_cases: Crime gun court cases
        - fact_traces: Individual firearm traces
        - view_dealer_summary: Analysis-ready dealer summary
        - view_jurisdiction: Jurisdiction nexus analysis
    """
    print("=" * 70)
    print("BRADY RELATIONAL ETL PIPELINE")
    print("=" * 70)

    out_path = Path(output_dir) if output_dir else Config.OUTPUT_DIR
    out_path.mkdir(parents=True, exist_ok=True)

    # Collect dealer DataFrames for merging
    dealer_dfs = []

    # Initialize empty fact tables
    fact_dl2 = pd.DataFrame()
    fact_cases = pd.DataFrame()
    fact_traces = pd.DataFrame()

    # 1. Extract Demand Letters
    if demand_letters_path and Path(demand_letters_path).exists():
        print("\n[1/4] Processing Demand Letters...")
        dealers, dl2 = extract_demand_letters(demand_letters_path)
        dealer_dfs.append(dealers)
        fact_dl2 = dl2
    else:
        print("\n[1/4] Skipping Demand Letters (not found)")

    # 2. Extract Crime Gun DB
    if crime_gun_path and Path(crime_gun_path).exists():
        print("\n[2/4] Processing Crime Gun Database...")
        dealers, cases = extract_crime_gun_db(crime_gun_path)
        dealer_dfs.append(dealers)
        fact_cases = cases
    else:
        print("\n[2/4] Skipping Crime Gun DB (not found)")

    # 3. Extract PA Traces (CSV)
    if pa_trace_csv_path and Path(pa_trace_csv_path).exists():
        print("\n[3/4] Processing PA Trace CSV...")
        dealers, traces = extract_pa_traces(pa_trace_csv_path, 'csv', max_trace_rows)
        dealer_dfs.append(dealers)
        fact_traces = pd.concat([fact_traces, traces], ignore_index=True)
    else:
        print("\n[3/4] Skipping PA Trace CSV (not found)")

    # 4. Extract PA Traces (XLSX)
    if pa_trace_xlsx_path and Path(pa_trace_xlsx_path).exists():
        print("\n[4/4] Processing PA Trace XLSX...")
        dealers, traces = extract_pa_traces(pa_trace_xlsx_path, 'xlsx', max_trace_rows)
        dealer_dfs.append(dealers)
        fact_traces = pd.concat([fact_traces, traces], ignore_index=True)
    else:
        print("\n[4/4] Skipping PA Trace XLSX (not found)")

    # Create unified dealer dimension
    if dealer_dfs:
        dim_dealers = create_dealer_dimension(dealer_dfs)
    else:
        dim_dealers = pd.DataFrame()

    # Create analysis views
    dealer_summary = create_dealer_summary(dim_dealers, fact_dl2, fact_traces)
    jurisdiction_analysis = create_jurisdiction_analysis(fact_traces, dim_dealers)

    # Save outputs
    print("\n" + "=" * 70)
    print("SAVING OUTPUT FILES...")
    print("=" * 70)

    # Save to Excel with multiple sheets
    with pd.ExcelWriter(out_path / 'brady_relational_database.xlsx', engine='openpyxl') as writer:
        if not dim_dealers.empty:
            dim_dealers.to_excel(writer, sheet_name='dim_dealers', index=False)
        if not fact_dl2.empty:
            fact_dl2.to_excel(writer, sheet_name='fact_dl2', index=False)
        if not fact_cases.empty:
            fact_cases.to_excel(writer, sheet_name='fact_cases', index=False)
        if not fact_traces.empty:
            # Limit traces sheet to 100k rows for Excel
            fact_traces.head(100000).to_excel(writer, sheet_name='fact_traces_sample', index=False)
        if not dealer_summary.empty:
            dealer_summary.to_excel(writer, sheet_name='view_dealer_summary', index=False)
        if not jurisdiction_analysis.empty:
            jurisdiction_analysis.to_excel(writer, sheet_name='view_jurisdiction', index=False)

    # Save full traces to CSV (can handle larger files)
    if not fact_traces.empty:
        fact_traces.to_csv(out_path / 'fact_traces_full.csv', index=False)

    # Save dealer summary
    dealer_summary.to_csv(out_path / 'dealer_summary.csv', index=False)

    print(f"\nFiles saved to: {out_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Unique Dealers:        {len(dim_dealers)}")
    print(f"DL2 Participation:     {len(fact_dl2)} records")
    print(f"Court Cases:           {len(fact_cases)} records")
    print(f"Firearm Traces:        {len(fact_traces)} records")
    print(f"")
    print("Top 10 High-Risk Dealers:")
    if not dealer_summary.empty:
        print(dealer_summary[['license_name', 'state', 'total_traces',
                              'short_ttc_count', 'in_dl2_program', 'risk_score']].head(10).to_string())

    return {
        'dim_dealers': dim_dealers,
        'fact_dl2': fact_dl2,
        'fact_cases': fact_cases,
        'fact_traces': fact_traces,
        'view_dealer_summary': dealer_summary,
        'view_jurisdiction': jurisdiction_analysis,
    }


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Brady Relational ETL Pipeline')
    parser.add_argument('--demand-letters', type=str, help='Path to Demand Letters Excel')
    parser.add_argument('--crime-gun', type=str, help='Path to Crime Gun DB Excel')
    parser.add_argument('--pa-trace-csv', type=str, help='Path to PA Trace CSV')
    parser.add_argument('--pa-trace-xlsx', type=str, help='Path to PA Trace XLSX')
    parser.add_argument('--output-dir', type=str, default='./brady_relational_output')
    parser.add_argument('--max-rows', type=int, help='Limit trace rows (for testing)')

    args = parser.parse_args()

    run_relational_etl(
        demand_letters_path=args.demand_letters,
        crime_gun_path=args.crime_gun,
        pa_trace_csv_path=args.pa_trace_csv,
        pa_trace_xlsx_path=args.pa_trace_xlsx,
        output_dir=args.output_dir,
        max_trace_rows=args.max_rows,
    )
