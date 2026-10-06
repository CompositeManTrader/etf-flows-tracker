"""Fetch shares outstanding from each ticker's single official source and validate it."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from config.universe import get_tickers
from data.sources import source_for

MIN_SHARES = 100_000  # no listed ETF in the universe is anywhere near this small


def _validate(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    ok = (
        df["as_of_date"].notna()
        & np.isfinite(pd.to_numeric(df["shares_outstanding"], errors="coerce"))
        & (pd.to_numeric(df["shares_outstanding"], errors="coerce") >= MIN_SHARES)
    )
    return df[ok], int((~ok).sum())


def fetch_all(tickers: list[str] | None = None, sleep: float = 0.4) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (observations, per-ticker status). Never substitutes one source for another."""
    tickers = tickers or get_tickers()
    run_at = pd.Timestamp.now(tz="UTC").tz_localize(None)
    obs, status = [], []

    for t in tickers:
        src = source_for(t)
        row = {"ticker": t, "source": src[0] if src else None, "rows": 0,
               "last_as_of": pd.NaT, "run_at": run_at, "detail": ""}
        if src is None:
            status.append({**row, "status": "no_source"})
            continue
        name, fetch = src
        try:
            df = fetch(t)
            df, rejected = _validate(df)
            if df.empty:
                status.append({**row, "status": "rejected", "detail": f"{rejected} rows failed validation"})
            else:
                df = df.assign(ticker=t, source=name, fetched_at=run_at)
                if "as_of_inferred" not in df:
                    df["as_of_inferred"] = False
                obs.append(df)
                status.append({**row, "status": "ok", "rows": len(df), "last_as_of": df["as_of_date"].max(),
                               "detail": f"{rejected} rejected" if rejected else ""})
        except Exception as e:  # noqa: BLE001
            status.append({**row, "status": "error", "detail": f"{type(e).__name__}: {e}"[:200]})
        time.sleep(sleep)

    obs_df = pd.concat(obs, ignore_index=True) if obs else pd.DataFrame()
    return obs_df, pd.DataFrame(status)
