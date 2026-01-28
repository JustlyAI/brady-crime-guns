#!/usr/bin/env python3
"""Tests for brady.etl.date_utils module."""

from datetime import date
import pytest

from brady.etl.date_utils import parse_purchase_date, calculate_crime_date, parse_time_to_recovery


class TestParsePurchaseDate:
    """Tests for parse_purchase_date function."""

    def test_short_year_2020s(self):
        """Two-digit years 00-26 should map to 2000-2026."""
        assert parse_purchase_date("7/2/20") == date(2020, 7, 2)
        assert parse_purchase_date("1/1/00") == date(2000, 1, 1)
        assert parse_purchase_date("5/15/26") == date(2026, 5, 15)

    def test_short_year_1900s(self):
        """Two-digit years 27-99 should map to 1927-1999."""
        assert parse_purchase_date("10/21/82") == date(1982, 10, 21)
        assert parse_purchase_date("12/31/99") == date(1999, 12, 31)
        assert parse_purchase_date("5/15/27") == date(1927, 5, 15)

    def test_four_digit_year(self):
        """Four-digit years should work directly."""
        assert parse_purchase_date("03/13/2020") == date(2020, 3, 13)
        assert parse_purchase_date("12/25/1999") == date(1999, 12, 25)

    def test_invalid_input(self):
        """Invalid inputs should return None."""
        assert parse_purchase_date("") is None
        assert parse_purchase_date(None) is None
        assert parse_purchase_date("invalid") is None
        assert parse_purchase_date("13/32/20") is None  # Invalid month/day


class TestParseTimeToRecovery:
    """Tests for parse_time_to_recovery function."""

    def test_string_numbers(self):
        """String numbers should parse correctly."""
        assert parse_time_to_recovery("1230") == 1230
        assert parse_time_to_recovery("500") == 500
        assert parse_time_to_recovery("0") == 0

    def test_integer_input(self):
        """Integer inputs should pass through."""
        assert parse_time_to_recovery(1000) == 1000
        assert parse_time_to_recovery(0) == 0

    def test_float_input(self):
        """Float inputs should be truncated to int."""
        assert parse_time_to_recovery(1500.5) == 1500
        assert parse_time_to_recovery(365.9) == 365

    def test_invalid_values(self):
        """Invalid values should return None."""
        assert parse_time_to_recovery("unknown") is None
        assert parse_time_to_recovery("N/A") is None
        assert parse_time_to_recovery("") is None
        assert parse_time_to_recovery(None) is None

    def test_suffix_handling(self):
        """Days suffix should be stripped."""
        assert parse_time_to_recovery("365 days") == 365
        assert parse_time_to_recovery("30 day") == 30


class TestCalculateCrimeDate:
    """Tests for calculate_crime_date function."""

    def test_basic_calculation(self):
        """Basic date addition should work."""
        sale = date(2020, 1, 15)
        crime = calculate_crime_date(sale, 365)
        assert crime == date(2021, 1, 14)

    def test_leap_year(self):
        """Leap year crossing should work correctly."""
        sale = date(2020, 2, 28)
        crime = calculate_crime_date(sale, 1)
        assert crime == date(2020, 2, 29)

    def test_year_boundary(self):
        """Year boundary crossing should work."""
        sale = date(2020, 12, 31)
        crime = calculate_crime_date(sale, 1)
        assert crime == date(2021, 1, 1)
