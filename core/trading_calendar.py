"""NYSE trading calendar helpers (dependency-free).

Holidays are hardcoded; extend the set each year.
"""
from __future__ import annotations

import pandas as pd

NYSE_HOLIDAYS = {pd.Timestamp(d) for d in (
    # 2024
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27", "2024-06-19",
    "2024-07-04", "2024-09-02", "2024-11-28", "2024-12-25",
    # 2025
    "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
    # 2026
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19",
    "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
    # 2027
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31", "2027-06-18",
    "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24",
)}

_NY = "America/New_York"
_CLOSE_BUFFER = pd.Timedelta(hours=16, minutes=30)  # NAVs/shares are struck after 16:00 ET


def is_trading_day(d) -> bool:
    d = pd.Timestamp(d).normalize()
    return d.weekday() < 5 and d not in NYSE_HOLIDAYS


def trading_days(start, end) -> pd.DatetimeIndex:
    """Trading days in [start, end]."""
    days = pd.bdate_range(pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize())
    return days[~days.isin(list(NYSE_HOLIDAYS))]


def trading_days_between(prev, curr) -> int:
    """Number of trading days in (prev, curr]. 1 means consecutive sessions."""
    if pd.isna(prev) or pd.isna(curr):
        return 0
    prev, curr = pd.Timestamp(prev).normalize(), pd.Timestamp(curr).normalize()
    if curr <= prev:
        return 0
    return len(trading_days(prev + pd.Timedelta(days=1), curr))


def previous_trading_day(d) -> pd.Timestamp:
    d = pd.Timestamp(d).normalize() - pd.Timedelta(days=1)
    while not is_trading_day(d):
        d -= pd.Timedelta(days=1)
    return d


def last_completed_session(now=None) -> pd.Timestamp:
    """Most recent NYSE session whose close (plus buffer) has passed, in ET, tz-naive."""
    now = pd.Timestamp.now(tz=_NY) if now is None else pd.Timestamp(now).tz_convert(_NY)
    today = now.normalize().tz_localize(None)
    after_close = (now - now.normalize()) >= _CLOSE_BUFFER
    if is_trading_day(today) and after_close:
        return today
    return previous_trading_day(today)
