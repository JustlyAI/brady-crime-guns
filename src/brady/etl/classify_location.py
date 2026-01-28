#!/usr/bin/env python3
"""
Crime Location Classifier - Batch Processing Script

Classifies crime location fields for DE Gunstat records:
- crime_location_state
- crime_location_city
- crime_location_zip
- crime_location_court
- crime_location_pd
- crime_location_reasoning

Usage:
    uv run python -m brady.etl.classify_location --batch-size 50
    uv run python -m brady.etl.classify_location --batch-size 20 --dry-run
"""

import argparse
import re
import sqlite3
from typing import Optional
from termcolor import cprint

from brady.etl.database import get_db_path
from brady.etl.court_lookup import lookup_court


# Enhanced Wilmington ZIP code mapping
# Based on actual Wilmington geography
WILMINGTON_STREET_TO_ZIP = {
    # 19801 - Downtown, West Side, Center City
    '19801': {
        'streets': [
            # Downtown core
            'market st', 'king st', 'walnut st', 'french st', 'shipley st',
            'orange st', 'tatnall st', 'west st', 'adams st',
            # West side numbered streets
            'w. 2nd', 'w. 3rd', 'w. 4th', 'w. 5th', 'w. 6th', 'w. 7th',
            'w. 8th', 'w. 9th', 'w 2nd', 'w 3rd', 'w 4th', 'w 5th', 'w 6th',
            'w 7th', 'w 8th', 'w 9th', 'west 2nd', 'west 3rd', 'west 4th',
            'west 5th', 'west 6th', 'west 7th', 'west 8th', 'west 9th',
            # South side
            's. walnut', 's walnut', 'south walnut',
            's. market', 's market', 'south market',
            # Specific downtown locations
            'rodney square', 'wilmington train', 'amtrak',
        ],
        'patterns': [
            r'\b[1-9]00\s+block\s+of\s+(market|king|walnut|french)',
            r'\bdowntown\b',
        ],
    },

    # 19802 - East Side, Northeast, Riverside
    '19802': {
        'streets': [
            # East side numbered streets
            'e. 2nd', 'e. 3rd', 'e. 4th', 'e. 5th', 'e. 6th', 'e. 7th',
            'e. 8th', 'e. 9th', 'e. 10th', 'e. 11th', 'e. 12th', 'e. 13th',
            'e. 14th', 'e. 15th', 'e. 16th', 'e. 17th', 'e. 18th',
            'e 2nd', 'e 3rd', 'e 4th', 'e 5th', 'e 6th', 'e 7th',
            'e 8th', 'e 9th', 'e 10th', 'e 11th', 'e 12th', 'e 13th',
            'east 2nd', 'east 3rd', 'east 4th', 'east 5th', 'east 6th',
            'east 7th', 'east 8th', 'east 9th', 'east 10th', 'east 11th',
            'east 12th', 'east 13th', 'east 14th', 'east 15th', 'east 16th',
            # North side streets (president names)
            'n. pine', 'n pine', 'north pine', 'pine st',
            'n. van buren', 'n van buren', 'van buren',
            'n. madison', 'n madison', 'madison st',
            'n. jackson', 'n jackson', 'jackson st',
            'n. monroe', 'n monroe', 'monroe st',
            'n. jefferson', 'n jefferson',
            'n. washington', 'n washington',
            'n. dupont', 'n dupont', 'north dupont',
            # Northeast area
            'north park', 'northeast blvd', 'governor printz',
            'edgemoor', 'claymont',
            # Riverside
            'riverside', 'brandywine',
            # South van buren area
            's. van buren', 's van buren', 'south van buren',
            'sycamore',
        ],
        'patterns': [
            r'\beast\s+side\b',
            r'\bnortheast\b',
            r'\briverside\b',
        ],
    },

    # 19805 - Prices Corner, Southwest
    '19805': {
        'streets': [
            'kirkwood hwy', 'kirkwood highway', 'prices corner',
            'greenbank', 'elsmere',
        ],
        'patterns': [
            r'\bprices\s+corner\b',
            r'\bsouthwest\b',
        ],
    },

    # 19806 - Trolley Square, Northwest, Highlands
    '19806': {
        'streets': [
            # Higher numbered west streets
            'w. 18th', 'w. 19th', 'w. 20th', 'w. 21st', 'w. 22nd',
            'w. 23rd', 'w. 24th', 'w. 25th', 'w. 26th', 'w. 27th',
            'w. 28th', 'w. 29th', 'w. 30th', 'w. 31st', 'w. 32nd',
            'w. 33rd', 'w. 34th', 'w. 35th', 'w. 36th', 'w. 37th',
            'w 18th', 'w 19th', 'w 20th', 'w 21st', 'w 22nd',
            'w 23rd', 'w 24th', 'w 25th', 'w 26th', 'w 27th',
            'w 28th', 'w 29th', 'w 30th', 'w 31st', 'w 32nd',
            'w 33rd', 'w 34th', 'w 35th', 'w 36th', 'w 37th',
            'west 18th', 'west 19th', 'west 20th', 'west 21st',
            # Northwest streets
            'delaware ave', 'lovering ave', 'pennsylvania ave',
            'baynard blvd', 'trolley square', 'wawaset',
            'highlands', 'rockford park',
        ],
        'patterns': [
            r'\btrolley\s+square\b',
            r'\bhighlands\b',
            r'\bnorthwest\b',
        ],
    },
}

# Default ZIP when no match found
DEFAULT_WILMINGTON_ZIP = '19801'


def infer_zip_from_narrative(narrative: Optional[str], city: str = 'Wilmington') -> tuple[str, str]:
    """
    Infer ZIP code from case narrative.

    Returns:
        tuple of (zip_code, method_description)
    """
    if not narrative or city != 'Wilmington':
        return DEFAULT_WILMINGTON_ZIP, 'Default (no narrative or non-Wilmington)'

    narrative_lower = narrative.lower()

    # Check each ZIP code's patterns
    for zip_code, rules in WILMINGTON_STREET_TO_ZIP.items():
        # Check street names
        for street in rules['streets']:
            if street in narrative_lower:
                return zip_code, f'Street match: {street}'

        # Check regex patterns
        for pattern in rules.get('patterns', []):
            if re.search(pattern, narrative_lower):
                return zip_code, f'Pattern match: {pattern}'

    # No match found - use default
    return DEFAULT_WILMINGTON_ZIP, 'Default (no street match)'


def classify_record(record: dict) -> dict:
    """
    Classify a single record's crime location.

    Args:
        record: Dict with keys from database row

    Returns:
        Dict with classification results
    """
    # State: Always DE for DE_GUNSTAT dataset
    state = 'DE'
    state_method = 'DE_GUNSTAT dataset implies Delaware'

    # City: From jurisdiction_city or default to Wilmington
    city = record.get('jurisdiction_city') or 'Wilmington'
    city_method = 'From jurisdiction_city' if record.get('jurisdiction_city') else 'Default for DE_GUNSTAT'

    # ZIP: Enhanced street matching
    zip_code, zip_method = infer_zip_from_narrative(record.get('case_summary'), city)

    # Court: From case number prefix lookup
    case_number = record.get('case_number')
    court = lookup_court(case_number)
    if court:
        court_method = f'Case prefix lookup ({case_number[:2] if case_number else "N/A"})'
    else:
        court = 'Delaware Superior Court'
        court_method = 'Default for felony cases'

    # Police Department: From city
    pd = f'{city} Police Department'
    pd_method = f'Derived from city ({city})'

    # Build structured reasoning
    reasoning = f'State: {state_method}. City: {city_method}. ZIP: {zip_method}. Court: {court_method}. PD: {pd_method}'

    return {
        'state': state,
        'city': city,
        'zip_code': zip_code,
        'court': court,
        'pd': pd,
        'reasoning': reasoning,
    }


def process_batch(batch_size: int = 50, dry_run: bool = False, verbose: bool = False) -> int:
    """
    Process a batch of unclassified records.

    Args:
        batch_size: Number of records to process
        dry_run: If True, don't write to database
        verbose: If True, print each classification

    Returns:
        Number of records processed
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get unclassified records
    cprint(f"Querying unclassified records (batch_size={batch_size})...", "yellow")

    cursor = conn.execute("""
        SELECT rowid, source_row, source_dataset, jurisdiction_state, jurisdiction_city,
               case_number, case_summary
        FROM crime_gun_events
        WHERE crime_location_state IS NULL
        LIMIT ?
    """, (batch_size,))

    records = cursor.fetchall()
    cprint(f"Found {len(records)} unclassified records", "cyan")

    if not records:
        cprint("No unclassified records found!", "green")
        conn.close()
        return 0

    processed = 0
    for record in records:
        record_dict = dict(record)
        rowid = record_dict['rowid']

        # Classify the record
        result = classify_record(record_dict)

        if verbose:
            cprint(f"\nRow {record_dict['source_row']} (rowid={rowid}):", "white")
            cprint(f"  State: {result['state']}", "green")
            cprint(f"  City:  {result['city']}", "green")
            cprint(f"  ZIP:   {result['zip_code']}", "green")
            cprint(f"  Court: {result['court']}", "green")
            cprint(f"  PD:    {result['pd']}", "green")
            if record_dict.get('case_summary'):
                summary_preview = record_dict['case_summary'][:100].replace('\n', ' ')
                cprint(f"  Narrative: {summary_preview}...", "white", attrs=["dark"])

        if not dry_run:
            conn.execute("""
                UPDATE crime_gun_events
                SET crime_location_state = ?,
                    crime_location_city = ?,
                    crime_location_zip = ?,
                    crime_location_court = ?,
                    crime_location_pd = ?,
                    crime_location_reasoning = ?
                WHERE rowid = ?
            """, (
                result['state'],
                result['city'],
                result['zip_code'],
                result['court'],
                result['pd'],
                result['reasoning'],
                rowid
            ))

        processed += 1

        # Progress indicator every 100 records
        if processed % 100 == 0:
            cprint(f"  Processed {processed}/{len(records)}...", "yellow")

    if not dry_run:
        conn.commit()
        cprint(f"\nCommitted {processed} updates to database", "green")
    else:
        cprint(f"\nDRY RUN: Would have updated {processed} records", "yellow")

    conn.close()
    return processed


def get_classification_stats() -> dict:
    """Get current classification statistics."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)

    stats = {}

    # Total and classified counts
    cursor = conn.execute("SELECT COUNT(*) FROM crime_gun_events")
    stats['total'] = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM crime_gun_events WHERE crime_location_state IS NOT NULL")
    stats['classified'] = cursor.fetchone()[0]

    stats['remaining'] = stats['total'] - stats['classified']
    stats['progress_pct'] = (stats['classified'] / stats['total'] * 100) if stats['total'] > 0 else 0

    # ZIP code distribution
    cursor = conn.execute("""
        SELECT crime_location_zip, COUNT(*) as count
        FROM crime_gun_events
        WHERE crime_location_zip IS NOT NULL
        GROUP BY crime_location_zip
        ORDER BY count DESC
    """)
    stats['zip_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description='Classify crime location fields for DE Gunstat records')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of records to process (default: 50)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing to database')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print each classification')
    parser.add_argument('--all', action='store_true', help='Process all remaining records')
    parser.add_argument('--stats', action='store_true', help='Show classification statistics only')

    args = parser.parse_args()

    cprint("=" * 60, "cyan")
    cprint("CRIME LOCATION CLASSIFIER", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")

    if args.stats:
        stats = get_classification_stats()
        print(f"\nClassification Status:")
        print(f"  Total records:    {stats['total']}")
        print(f"  Classified:       {stats['classified']}")
        print(f"  Remaining:        {stats['remaining']}")
        print(f"  Progress:         {stats['progress_pct']:.1f}%")
        if stats['zip_distribution']:
            print(f"\nZIP Code Distribution:")
            for zip_code, count in stats['zip_distribution'].items():
                print(f"  {zip_code}: {count}")
        return

    if args.all:
        # Process all remaining records in batches
        total_processed = 0
        batch_num = 1

        while True:
            cprint(f"\n--- Batch {batch_num} ---", "cyan")
            processed = process_batch(
                batch_size=args.batch_size,
                dry_run=args.dry_run,
                verbose=args.verbose
            )

            if processed == 0:
                break

            total_processed += processed
            batch_num += 1

            # Show progress
            stats = get_classification_stats()
            cprint(f"Progress: {stats['classified']}/{stats['total']} ({stats['progress_pct']:.1f}%)", "green")

        cprint(f"\n{'=' * 60}", "cyan")
        cprint(f"COMPLETE: Processed {total_processed} records total", "green", attrs=["bold"])

    else:
        # Process single batch
        processed = process_batch(
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            verbose=args.verbose
        )

        # Show final stats
        stats = get_classification_stats()
        print(f"\nCurrent Status:")
        print(f"  Classified: {stats['classified']}/{stats['total']} ({stats['progress_pct']:.1f}%)")
        print(f"  Remaining:  {stats['remaining']}")


if __name__ == '__main__':
    main()
