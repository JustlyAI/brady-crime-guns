#!/usr/bin/env python3
"""
Brady ETL - Court Lookup Utilities

Court lookup table and case number normalization for Delaware courts.
"""

import re
from typing import Optional
from termcolor import cprint


# Delaware Court Lookup Table
# Case number format: XX-YY-NNNNNN where XX is court prefix
COURT_LOOKUP = {
    "10": "Delaware Supreme Court",
    "19": "Delaware Family Court",
    "30": "Delaware Superior Court",
    "31": "Court of Common Pleas",
}


def lookup_court(case_number: str) -> Optional[str]:
    """
    Look up court name from case number prefix.

    Args:
        case_number: Case number like "30-23-063056"

    Returns:
        Court name or None if not found
    """
    if not case_number or not isinstance(case_number, str):
        return None

    case_number = case_number.strip()
    if not case_number:
        return None

    # Extract prefix (first 2 digits before dash)
    match = re.match(r'^(\d{2})-', case_number)
    if not match:
        return None

    prefix = match.group(1)
    return COURT_LOOKUP.get(prefix)


def normalize_case_number(case_number: str) -> Optional[str]:
    """
    Normalize case number to standard format: XX-YY-NNNNNN

    - Strips whitespace
    - Validates format
    - Pads sequence number to 6 digits

    Args:
        case_number: Raw case number string

    Returns:
        Normalized case number or None if invalid
    """
    if not case_number or not isinstance(case_number, str):
        return None

    # Clean up
    case_number = case_number.strip()
    if not case_number:
        return None

    # Try to match expected format: XX-YY-NNNNNN (with flexible sequence length)
    match = re.match(r'^(\d{2})-(\d{2})-(\d+)$', case_number)
    if not match:
        # Try alternate formats
        # XX-YY-NNNNNN with spaces
        case_number = re.sub(r'\s+', '', case_number)
        match = re.match(r'^(\d{2})-(\d{2})-(\d+)$', case_number)

        if not match:
            return None

    court_prefix = match.group(1)
    year = match.group(2)
    sequence = match.group(3)

    # Pad sequence to 6 digits
    sequence = sequence.zfill(6)

    return f"{court_prefix}-{year}-{sequence}"


def get_case_year(case_number: str) -> Optional[int]:
    """
    Extract the year from a case number.

    Args:
        case_number: Case number like "30-23-063056"

    Returns:
        Full year (e.g., 2023) or None
    """
    if not case_number or not isinstance(case_number, str):
        return None

    match = re.match(r'^\d{2}-(\d{2})-\d+$', case_number.strip())
    if not match:
        return None

    year_suffix = int(match.group(1))

    # Assume 2000s for now (00-99 -> 2000-2099)
    # Adjust if we encounter older cases
    if year_suffix <= 26:
        return 2000 + year_suffix
    else:
        return 1900 + year_suffix


if __name__ == "__main__":
    cprint("=" * 60, "cyan")
    cprint("TESTING COURT LOOKUP UTILITIES", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")

    # Test case numbers
    test_cases = [
        "30-23-063056",    # Delaware Superior Court
        "31-22-012345",    # Court of Common Pleas
        "10-21-000001",    # Delaware Supreme Court
        "19-20-005678",    # Delaware Family Court
        "30-23-1234",      # Short sequence (should pad)
        " 30-23-063056 ",  # With whitespace
        "invalid",
        "",
        None,
    ]

    print("\nCourt Lookup Tests:")
    for case in test_cases:
        court = lookup_court(case)
        print(f"  '{case}' -> {court}")

    print("\nCase Number Normalization Tests:")
    for case in test_cases:
        normalized = normalize_case_number(case)
        print(f"  '{case}' -> '{normalized}'")

    print("\nCase Year Extraction Tests:")
    for case in test_cases:
        year = get_case_year(case)
        print(f"  '{case}' -> {year}")

    print("\nCourt Lookup Table:")
    for prefix, name in COURT_LOOKUP.items():
        print(f"  {prefix}: {name}")

    cprint("\n✅ Court lookup utilities tests complete!", "green", attrs=["bold"])
