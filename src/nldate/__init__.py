import calendar
import re
from datetime import date, timedelta

__all__ = ["parse"]

WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

MONTHS: dict[str, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

# Ordered longest-first to avoid short alternatives shadowing longer ones.
_WORD_NUMBERS: dict[str, int] = {
    "twelve": 12,
    "eleven": 11,
    "three": 3,
    "seven": 7,
    "eight": 8,
    "four": 4,
    "five": 5,
    "nine": 9,
    "six": 6,
    "two": 2,
    "ten": 10,
    "one": 1,
    "an": 1,
    "a": 1,
}

_WORD_NUM_RE = r"(\d+|" + "|".join(_WORD_NUMBERS.keys()) + r")"
_MONTH_RE = "|".join(MONTHS.keys())
_WEEKDAY_RE = "|".join(WEEKDAYS.keys())


def _add_months(d: date, months: int) -> date:
    """Add a signed number of months to a date, clamping the day if needed."""
    total = d.year * 12 + (d.month - 1) + months
    year, month = total // 12, total % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _to_int(s: str) -> int | None:
    s = s.lower().strip()
    if s.isdigit():
        return int(s)
    return _WORD_NUMBERS.get(s)


def _apply_offset(base: date, days: int, months: int, sign: int) -> date:
    result = base
    if months:
        result = _add_months(result, sign * months)
    if days:
        result = result + timedelta(days=sign * days)
    return result


def _parse_offset_str(s: str) -> tuple[int, int] | None:
    """Parse '5 days', '1 year and 2 months', etc. Returns (days, months)."""
    s = s.lower().strip()
    parts = re.split(r"\s+and\s+", s)
    total_days = 0
    total_months = 0
    for part in parts:
        part = part.strip()
        m = re.fullmatch(
            _WORD_NUM_RE + r"\s+(days?|weeks?|months?|years?)",
            part,
        )
        if not m:
            return None
        n = _to_int(m.group(1))
        if n is None:
            return None
        unit = m.group(2).lower()
        if unit.startswith("day"):
            total_days += n
        elif unit.startswith("week"):
            total_days += n * 7
        elif unit.startswith("month"):
            total_months += n
        elif unit.startswith("year"):
            total_months += n * 12
    return (total_days, total_months)


def _parse_absolute(s: str) -> date | None:
    """Parse absolute date strings (ISO, named-month, numeric)."""
    s = s.strip()

    # ISO with dashes or slashes: YYYY-MM-DD or YYYY/MM/DD
    m = re.fullmatch(r"(\d{4})[/\-](\d{2})[/\-](\d{2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # Numeric: MM/DD/YYYY or MM-DD-YYYY
    m = re.fullmatch(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", s)
    if m:
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))

    # Month DD[st/nd/rd/th][,] YYYY  e.g. "December 1st, 2025"
    m = re.fullmatch(
        rf"({_MONTH_RE})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})",
        s,
        re.IGNORECASE,
    )
    if m:
        month = MONTHS[m.group(1).lower()]
        return date(int(m.group(3)), month, int(m.group(2)))

    # DD[st/nd/rd/th] Month YYYY  e.g. "1st December 2025"
    m = re.fullmatch(
        rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_RE})\s+(\d{{4}})",
        s,
        re.IGNORECASE,
    )
    if m:
        month = MONTHS[m.group(2).lower()]
        return date(int(m.group(3)), month, int(m.group(1)))

    return None


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural-language date string and return a ``datetime.date``.

    Args:
        s: A natural-language date string, e.g. "next Tuesday",
           "5 days before December 1st, 2025", or "in 3 weeks".
        today: Reference date for relative expressions.  Defaults to the
               current date when not provided.

    Returns:
        The resolved ``datetime.date``.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    if today is None:
        today = date.today()

    norm = s.strip()
    low = norm.lower()

    # ── Simple keywords ──────────────────────────────────────────────────────
    if low in ("today", "now"):
        return today
    if low == "tomorrow":
        return today + timedelta(days=1)
    if low == "yesterday":
        return today - timedelta(days=1)

    # ── next/last week | month | year ────────────────────────────────────────
    m = re.fullmatch(r"(next|last)\s+(week|month|year)", low)
    if m:
        sign = 1 if m.group(1) == "next" else -1
        unit = m.group(2)
        if unit == "week":
            return today + timedelta(days=7 * sign)
        elif unit == "month":
            return _add_months(today, sign)
        else:
            return _add_months(today, 12 * sign)

    # ── next/last/this <weekday> ──────────────────────────────────────────────
    m = re.fullmatch(rf"(next|last|this)\s+({_WEEKDAY_RE})", low)
    if m:
        qualifier = m.group(1)
        target = WEEKDAYS[m.group(2)]
        current = today.weekday()
        if qualifier == "next":
            delta = (target - current) % 7 or 7
            return today + timedelta(days=delta)
        elif qualifier == "last":
            delta = (current - target) % 7 or 7
            return today - timedelta(days=delta)
        else:  # this
            delta = (target - current) % 7
            return today + timedelta(days=delta)

    # ── in N units ────────────────────────────────────────────────────────────
    m = re.fullmatch(rf"in\s+{_WORD_NUM_RE}\s+(days?|weeks?|months?|years?)", low)
    if m:
        n = _to_int(m.group(1))
        unit = m.group(2).lower()
        if n is not None:
            if unit.startswith("day"):
                return today + timedelta(days=n)
            elif unit.startswith("week"):
                return today + timedelta(days=n * 7)
            elif unit.startswith("month"):
                return _add_months(today, n)
            else:
                return _add_months(today, n * 12)

    # ── N units ago ───────────────────────────────────────────────────────────
    m = re.fullmatch(rf"{_WORD_NUM_RE}\s+(days?|weeks?|months?|years?)\s+ago", low)
    if m:
        n = _to_int(m.group(1))
        unit = m.group(2).lower()
        if n is not None:
            if unit.startswith("day"):
                return today - timedelta(days=n)
            elif unit.startswith("week"):
                return today - timedelta(days=n * 7)
            elif unit.startswith("month"):
                return _add_months(today, -n)
            else:
                return _add_months(today, -n * 12)

    # ── N units from <base> ───────────────────────────────────────────────────
    m = re.fullmatch(
        rf"{_WORD_NUM_RE}\s+(days?|weeks?|months?|years?)\s+from\s+(.+)", low
    )
    if m:
        n = _to_int(m.group(1))
        unit = m.group(2).lower()
        base_orig = norm[m.start(3) :]
        if n is not None:
            try:
                base = parse(base_orig, today)
            except ValueError:
                pass
            else:
                if unit.startswith("day"):
                    return base + timedelta(days=n)
                elif unit.startswith("week"):
                    return base + timedelta(days=n * 7)
                elif unit.startswith("month"):
                    return _add_months(base, n)
                else:
                    return _add_months(base, n * 12)

    # ── Absolute date ─────────────────────────────────────────────────────────
    result = _parse_absolute(norm)
    if result is not None:
        return result

    # ── <compound-offset> before/after <base> ────────────────────────────────
    bm = re.fullmatch(r"(.+?)\s+(before|after)\s+(.+)", low)
    if bm:
        offset_str = bm.group(1)
        direction = bm.group(2)
        base_orig = norm[bm.start(3) :]
        try:
            base = parse(base_orig, today)
        except ValueError:
            pass
        else:
            offset = _parse_offset_str(offset_str)
            if offset is not None:
                days, months = offset
                sign = -1 if direction == "before" else 1
                return _apply_offset(base, days, months, sign)

    raise ValueError(f"Cannot parse date string: {s!r}")
