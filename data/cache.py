"""Parquet store of official shares outstanding, keyed by (ticker, as_of_date).

as_of_date is the trading session the issuer says the number belongs to, not
the time the job ran. Re-running the job is idempotent: the latest fetch of a
given (ticker, as_of_date) replaces the previous one, and other sessions are
never touched, so delayed or repeated cron runs can't overwrite other days.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SHARES_DIR = Path(__file__).parent / "shares"
SHARES_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = SHARES_DIR / "history.parquet"
STATUS_FILE = SHARES_DIR / "last_run_status.parquet"
MONTHLY_FILE = SHARES_DIR / "vanguard_monthly.parquet"

RETENTION_DAYS = 400

HISTORY_COLUMNS = [
    "ticker", "as_of_date", "shares_outstanding", "nav", "source", "as_of_inferred", "fetched_at",
]


def load_history() -> pd.DataFrame:
    if not HISTORY_FILE.exists():
        return pd.DataFrame(columns=HISTORY_COLUMNS)
    df = pd.read_parquet(HISTORY_FILE)
    df["as_of_date"] = pd.to_datetime(df["as_of_date"])
    return df


def upsert_history(new: pd.DataFrame) -> pd.DataFrame:
    hist = load_history()
    new = new.copy()
    new["as_of_date"] = pd.to_datetime(new["as_of_date"]).dt.normalize()
    combined = pd.concat([hist, new[HISTORY_COLUMNS]], ignore_index=True)
    combined = combined.drop_duplicates(["ticker", "as_of_date"], keep="last")
    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=RETENTION_DAYS)
    combined = combined[combined["as_of_date"] >= cutoff]
    combined = combined.sort_values(["ticker", "as_of_date"]).reset_index(drop=True)
    combined.to_parquet(HISTORY_FILE, index=False)
    return combined


def save_status(status: pd.DataFrame) -> None:
    status.to_parquet(STATUS_FILE, index=False)


def load_status() -> pd.DataFrame:
    if not STATUS_FILE.exists():
        return pd.DataFrame(columns=["ticker", "source", "status", "detail", "rows", "last_as_of", "run_at"])
    return pd.read_parquet(STATUS_FILE)


def latest_as_of() -> pd.Timestamp | None:
    h = load_history()
    return None if h.empty else pd.Timestamp(h["as_of_date"].max())


def load_monthly() -> pd.DataFrame:
    if not MONTHLY_FILE.exists():
        return pd.DataFrame(columns=["ticker", "as_of_date", "shares_outstanding", "nav", "fetched_at"])
    df = pd.read_parquet(MONTHLY_FILE)
    df["as_of_date"] = pd.to_datetime(df["as_of_date"])
    return df


def upsert_monthly(new: pd.DataFrame) -> pd.DataFrame:
    """Month-end observations keyed by (ticker, as_of_date); kept indefinitely (12 rows/year/ticker)."""
    new = new.copy()
    new["as_of_date"] = pd.to_datetime(new["as_of_date"]).dt.normalize()
    combined = pd.concat([load_monthly(), new], ignore_index=True)
    combined["as_of_date"] = pd.to_datetime(combined["as_of_date"])  # concat with an empty frame drops the dtype
    combined["fetched_at"] = pd.to_datetime(combined["fetched_at"])
    # keep the first NAV we saw for a month end: later runs may no longer find it in the price history
    combined = combined.sort_values("fetched_at")
    nav_first = combined.dropna(subset=["nav"]).drop_duplicates(["ticker", "as_of_date"], keep="first")
    combined = combined.drop_duplicates(["ticker", "as_of_date"], keep="last").drop(columns=["nav"])
    combined = combined.merge(nav_first[["ticker", "as_of_date", "nav"]], on=["ticker", "as_of_date"], how="left")
    combined = combined.sort_values(["ticker", "as_of_date"]).reset_index(drop=True)
    combined.to_parquet(MONTHLY_FILE, index=False)
    return combined
