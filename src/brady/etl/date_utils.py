#!/usr/bin/env python3
"""
Brady ETL - Date Utilities

Date parsing and calculation utilities for crime gun data.
"""

from datetime import date, timedelta
from typing import Optional
import re
from termcolor import cprint


def parse_purchase_date(date_str: str) -> Optional[date]:
    """
    Parse M/D/YY or M/D/YYYY format to date object.

    Two-digit year handling:
        00-26 -> 2000-2026 (current era)
        27-99 -> 1927-1999 (historical)

    Args:
        date_str: Date string like "7/2/20" or "10/21/2020"

    Returns:
        date object or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Try M/D/YY or M/D/YYYY pattern
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', date_str)
    if not match:
        return None

    try:
        month = int(match.group(1))
        day = int(match.group(2))
        year = int(match.group(3))

        # Handle two-digit year
        if year < 100:
            if year <= 26:
                year += 2000
            else:
                year += 1900

        # Validate ranges
        if not (1 <= month <= 12):
            return None
        if not (1 <= day <= 31):
            return None
        if not (1900 <= year <= 2100):
            return None

        return date(year, month, day)
    except (ValueError, OverflowError) as e:
        cprint(f"  Warning: Could not parse date '{date_str}': {e}", "yellow")
        return None


def calculate_crime_date(sale_date: date, days: int) -> date:
    """
    Calculate crime date from sale date and time to recovery.

    Args:
        sale_date: The purchase/sale date
        days: Days between sale and crime (time_to_crime)

    Returns:
        Calculated crime date (sale_date + days)
    """
    return sale_date + timedelta(days=days)


def parse_time_to_recovery(ttr_str) -> Optional[int]:
    """
    Parse time to recovery string to integer days.

    Args:
        ttr_str: String like "1230" or integer, or "unknown"

    Returns:
        Integer days or None if not parseable
    """
    if ttr_str is None:
        return None

    # Already an int
    if isinstance(ttr_str, int):
        return ttr_str if ttr_str >= 0 else None

    # Already a float
    if isinstance(ttr_str, float):
        if ttr_str != ttr_str:  # NaN check
            return None
        return int(ttr_str) if ttr_str >= 0 else None

    # String parsing
    if not isinstance(ttr_str, str):
        return None

    ttr_str = ttr_str.strip().lower()

    # Handle known non-numeric values
    if ttr_str in ('unknown', 'n/a', 'na', '-', ''):
        return None

    # Remove any common suffixes/prefixes
    ttr_str = re.sub(r'\s*(days?|d)\s*$', '', ttr_str, flags=re.IGNORECASE)
    ttr_str = ttr_str.strip()

    try:
        value = int(float(ttr_str))
        return value if value >= 0 else None
    except (ValueError, OverflowError):
        return None


if __name__ == "__main__":
    # Test date parsing
    cprint("=" * 60, "cyan")
    cprint("TESTING DATE UTILITIES", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")

    test_dates = [
        "7/2/20",      # -> 2020-07-02
        "10/21/82",    # -> 1982-10-21
        "03/13/2020",  # -> 2020-03-13
        "1/1/00",      # -> 2000-01-01
        "12/31/99",    # -> 1999-12-31
        "5/15/26",     # -> 2026-05-15
        "5/15/27",     # -> 1927-05-15
        "",            # -> None
        None,          # -> None
        "invalid",     # -> None
    ]

    print("\nDate Parsing Tests:")
    for d in test_dates:
        result = parse_purchase_date(d)
        print(f"  '{d}' -> {result}")

    # Test TTR parsing
    test_ttr = [
        "1230",
        "500",
        1000,
        1500.5,
        "unknown",
        "N/A",
        "",
        None,
        "365 days",
    ]

    print("\nTTR Parsing Tests:")
    for t in test_ttr:
        result = parse_time_to_recovery(t)
        print(f"  '{t}' -> {result}")

    # Test crime date calculation
    print("\nCrime Date Calculation:")
    sale = date(2020, 1, 15)
    days = 365
    crime = calculate_crime_date(sale, days)
    print(f"  Sale: {sale} + {days} days = Crime: {crime}")

    cprint("\n✅ Date utilities tests complete!", "green", attrs=["bold"])
