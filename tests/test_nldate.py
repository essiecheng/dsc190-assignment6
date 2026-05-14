"""Tests for the nldate.parse() function.

Reference anchor: TODAY = date(2025, 1, 1) which is a Wednesday.
"""

from datetime import date

import pytest

from nldate import parse

TODAY = date(2025, 1, 1)  # Wednesday


# ── Keywords ──────────────────────────────────────────────────────────────────


def test_today() -> None:
    assert parse("today", today=TODAY) == TODAY


def test_tomorrow() -> None:
    assert parse("tomorrow", today=TODAY) == date(2025, 1, 2)


def test_yesterday() -> None:
    assert parse("yesterday", today=TODAY) == date(2024, 12, 31)


def test_now_alias() -> None:
    assert parse("now", today=TODAY) == TODAY


# ── Next / last weekday ───────────────────────────────────────────────────────


def test_next_tuesday() -> None:
    # Wednesday → next Tuesday is 6 days later
    assert parse("next Tuesday", today=TODAY) == date(2025, 1, 7)


def test_next_wednesday_skips_to_following_week() -> None:
    # "next Wednesday" when today IS Wednesday → 7 days later
    assert parse("next Wednesday", today=TODAY) == date(2025, 1, 8)


def test_last_monday() -> None:
    # Wednesday → last Monday is 2 days earlier
    assert parse("last Monday", today=TODAY) == date(2024, 12, 30)


def test_this_friday() -> None:
    # Wednesday → this Friday is 2 days later
    assert parse("this Friday", today=TODAY) == date(2025, 1, 3)


# ── Next / last calendar unit ─────────────────────────────────────────────────


def test_next_week() -> None:
    assert parse("next week", today=TODAY) == date(2025, 1, 8)


def test_last_month() -> None:
    assert parse("last month", today=TODAY) == date(2024, 12, 1)


def test_next_year() -> None:
    assert parse("next year", today=TODAY) == date(2026, 1, 1)


# ── Offset from today ─────────────────────────────────────────────────────────


def test_in_3_days() -> None:
    assert parse("in 3 days", today=TODAY) == date(2025, 1, 4)


def test_in_two_weeks() -> None:
    assert parse("in two weeks", today=TODAY) == date(2025, 1, 15)


def test_in_a_month() -> None:
    assert parse("in a month", today=TODAY) == date(2025, 2, 1)


def test_5_days_ago() -> None:
    assert parse("5 days ago", today=TODAY) == date(2024, 12, 27)


def test_3_months_ago() -> None:
    assert parse("3 months ago", today=TODAY) == date(2024, 10, 1)


def test_1_year_ago() -> None:
    assert parse("1 year ago", today=TODAY) == date(2024, 1, 1)


# ── N units from <base> ───────────────────────────────────────────────────────


def test_2_weeks_from_now() -> None:
    assert parse("2 weeks from now", today=TODAY) == date(2025, 1, 15)


def test_two_weeks_from_tomorrow() -> None:
    assert parse("two weeks from tomorrow", today=TODAY) == date(2025, 1, 16)


def test_10_days_from_yesterday() -> None:
    assert parse("10 days from yesterday", today=TODAY) == date(2025, 1, 10)


# ── Absolute dates ────────────────────────────────────────────────────────────


def test_iso_date() -> None:
    assert parse("2025-06-15") == date(2025, 6, 15)


def test_full_month_name_ordinal() -> None:
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_full_month_name_no_ordinal() -> None:
    assert parse("March 20, 2024") == date(2024, 3, 20)


def test_abbreviated_month() -> None:
    assert parse("Jan 5, 2024") == date(2024, 1, 5)


def test_dd_month_yyyy() -> None:
    assert parse("25th December 2025") == date(2025, 12, 25)


def test_numeric_date_slash() -> None:
    assert parse("12/25/2025") == date(2025, 12, 25)


# ── Offset before/after absolute date ────────────────────────────────────────


def test_days_before_absolute() -> None:
    # 5 days before December 1st, 2025 = November 26, 2025
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_days_after_absolute() -> None:
    assert parse("10 days after January 1st, 2025") == date(2025, 1, 11)


def test_weeks_before_absolute() -> None:
    assert parse("2 weeks before March 1, 2025") == date(2025, 2, 15)


def test_months_after_absolute() -> None:
    assert parse("3 months after January 1st, 2025") == date(2025, 4, 1)


# ── Compound offsets (before/after) ───────────────────────────────────────────


def test_compound_offset_after_yesterday() -> None:
    # yesterday = Dec 31, 2024; +1 year +2 months = Feb 28, 2026
    assert parse("1 year and 2 months after yesterday", today=TODAY) == date(
        2026, 2, 28
    )


def test_compound_offset_before_absolute() -> None:
    # 2 weeks and 3 days before March 1, 2025 = 17 days before = Feb 12, 2025
    assert parse("2 weeks and 3 days before March 1, 2025") == date(2025, 2, 12)


# ── Month-end clamping ────────────────────────────────────────────────────────


def test_month_clamp_jan31_plus_one_month() -> None:
    # Jan 31 + 1 month = Feb 28 (2025 is not a leap year)
    assert parse("next month", today=date(2025, 1, 31)) == date(2025, 2, 28)


def test_month_clamp_jan31_minus_one_month() -> None:
    # Jan 31 - 1 month = Dec 31, 2024
    assert parse("last month", today=date(2025, 1, 31)) == date(2024, 12, 31)


# ── Error handling ────────────────────────────────────────────────────────────


def test_invalid_string_raises() -> None:
    with pytest.raises(ValueError):
        parse("purple monkey dishwasher")
