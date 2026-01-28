#!/usr/bin/env python3
"""Tests for brady.etl.court_lookup module."""

import pytest

from brady.etl.court_lookup import lookup_court, normalize_case_number, get_case_year


class TestLookupCourt:
    """Tests for lookup_court function."""

    def test_known_courts(self):
        """Known court prefixes should return correct names."""
        assert lookup_court("30-23-063056") == "Delaware Superior Court"
        assert lookup_court("31-22-012345") == "Court of Common Pleas"
        assert lookup_court("10-21-000001") == "Delaware Supreme Court"
        assert lookup_court("19-20-005678") == "Delaware Family Court"

    def test_whitespace_handling(self):
        """Whitespace should be stripped."""
        assert lookup_court(" 30-23-063056 ") == "Delaware Superior Court"

    def test_invalid_input(self):
        """Invalid inputs should return None."""
        assert lookup_court("") is None
        assert lookup_court(None) is None
        assert lookup_court("invalid") is None
        assert lookup_court("99-23-000001") is None  # Unknown prefix


class TestNormalizeCaseNumber:
    """Tests for normalize_case_number function."""

    def test_already_normalized(self):
        """Already normalized case numbers should pass through."""
        assert normalize_case_number("30-23-063056") == "30-23-063056"
        assert normalize_case_number("31-22-012345") == "31-22-012345"

    def test_short_sequence_padding(self):
        """Short sequence numbers should be padded to 6 digits."""
        assert normalize_case_number("30-23-1234") == "30-23-001234"
        assert normalize_case_number("30-23-1") == "30-23-000001"

    def test_whitespace_handling(self):
        """Whitespace should be stripped."""
        assert normalize_case_number(" 30-23-063056 ") == "30-23-063056"

    def test_invalid_input(self):
        """Invalid inputs should return None."""
        assert normalize_case_number("") is None
        assert normalize_case_number(None) is None
        assert normalize_case_number("invalid") is None


class TestGetCaseYear:
    """Tests for get_case_year function."""

    def test_2000s_years(self):
        """Years 00-26 should map to 2000-2026."""
        assert get_case_year("30-23-063056") == 2023
        assert get_case_year("30-00-000001") == 2000
        assert get_case_year("30-26-000001") == 2026

    def test_1900s_years(self):
        """Years 27-99 should map to 1927-1999."""
        assert get_case_year("30-99-000001") == 1999
        assert get_case_year("30-27-000001") == 1927

    def test_invalid_input(self):
        """Invalid inputs should return None."""
        assert get_case_year("") is None
        assert get_case_year(None) is None
        assert get_case_year("invalid") is None
