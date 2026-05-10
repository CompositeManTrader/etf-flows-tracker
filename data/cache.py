"""Parquet-based persistence for daily shares-outstanding snapshots."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = SNAPSHOT_DIR / "shares_history.parquet"

_HISTORY_COLUMNS = ["ticker", "shares_outstanding", "fetched_at", "source", "snapshot_date"]


def save_daily_snapshot(df: pd.DataFrame, snapshot_date: pd.Timestamp | None = None) -> Path:
    if snapshot_date is None:
        snapshot_date = pd.Timestamp.utcnow().normalize()
    snapshot_date = pd.Timestamp(snapshot_date).normalize()

    df = df.copy()
    df["snapshot_date"] = snapshot_date

    daily_path = SNAPSHOT_DIR / f"shares_{snapshot_date.strftime('%Y-%m-%d')}.parquet"
    df.to_parquet(daily_path, index=False)

    if HISTORY_FILE.exists():
        history = pd.read_parquet(HISTORY_FILE)
        history = history[history["snapshot_date"] != snapshot_date]
        combined = pd.concat([history, df], ignore_index=True)
    else:
        combined = df

    for col in _HISTORY_COLUMNS:
        if col not in combined.columns:
            combined[col] = pd.NA

    combined = combined[_HISTORY_COLUMNS].sort_values(["ticker", "snapshot_date"])
    combined.to_parquet(HISTORY_FILE, index=False)
    return daily_path


def load_history() -> pd.DataFrame:
    if not HISTORY_FILE.exists():
        return pd.DataFrame(columns=_HISTORY_COLUMNS)
    return pd.read_parquet(HISTORY_FILE)


def latest_snapshot_date() -> pd.Timestamp | None:
    h = load_history()
    if h.empty or "snapshot_date" not in h.columns:
        return None
    val = h["snapshot_date"].max()
    if pd.isna(val):
        return None
    return pd.Timestamp(val)
