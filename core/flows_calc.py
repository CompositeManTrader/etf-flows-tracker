"""Core flow calculations: deltas × close, aggregations, z-scores, rotation."""
from __future__ import annotations

import pandas as pd

from config.universe import get_universe

_FLOW_COLS = [
    "date", "ticker", "name", "category", "subcategory", "issuer",
    "shares_outstanding", "prev_shares", "delta_shares", "close", "volume", "flow_usd",
]


def _to_naive_date(series: pd.Series) -> pd.Series:
    s = pd.to_datetime(series, errors="coerce", utc=False)
    tz = getattr(s.dt, "tz", None)
    if tz is not None:
        try:
            s = s.dt.tz_convert(None)
        except (TypeError, AttributeError):
            s = s.dt.tz_localize(None)
    return s.dt.normalize()


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    universe = get_universe()
    meta = pd.DataFrame.from_dict(universe, orient="index").reset_index().rename(columns={"index": "ticker"})
    return df.merge(meta, on="ticker", how="left")


def compute_daily_flows(shares_history: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    if shares_history is None or shares_history.empty:
        return pd.DataFrame(columns=_FLOW_COLS)

    h = shares_history.copy()
    h["snapshot_date"] = _to_naive_date(h["snapshot_date"])
    h = h.sort_values(["ticker", "snapshot_date"])
    h["prev_shares"] = h.groupby("ticker")["shares_outstanding"].shift(1)
    h["delta_shares"] = h["shares_outstanding"] - h["prev_shares"]

    if prices is None or prices.empty:
        merged = h.copy()
        merged["date"] = merged["snapshot_date"]
        merged["close"] = pd.NA
        merged["volume"] = pd.NA
    else:
        p = prices.copy()
        p["date"] = _to_naive_date(p["date"])
        merged = h.merge(
            p, left_on=["snapshot_date", "ticker"], right_on=["date", "ticker"], how="left"
        )
        if "date" not in merged.columns:
            merged["date"] = merged["snapshot_date"]
        else:
            merged["date"] = merged["date"].fillna(merged["snapshot_date"])

    merged["flow_usd"] = merged["delta_shares"] * merged["close"]
    merged = _enrich(merged)

    for col in _FLOW_COLS:
        if col not in merged.columns:
            merged[col] = pd.NA

    return merged[_FLOW_COLS].sort_values(["date", "ticker"]).reset_index(drop=True)


def _trading_day_cutoff(f: pd.DataFrame, n_days: int) -> pd.Timestamp:
    """Return the date that, used as `date >= cutoff`, yields the last N trading days.

    Operates on actual unique trading dates present in `f`, not calendar days.
    """
    trading_dates = sorted(pd.to_datetime(f["date"].dropna().unique()))
    if not trading_dates:
        return pd.Timestamp.min
    idx = max(0, len(trading_dates) - n_days)
    return pd.Timestamp(trading_dates[idx])


def aggregate_by_category(flows: pd.DataFrame, period_days: int = 1) -> pd.DataFrame:
    if flows is None or flows.empty:
        return pd.DataFrame(columns=["category", "flow_usd", "flow_usd_b"])

    f = flows.dropna(subset=["date", "flow_usd"]).copy()
    if f.empty:
        return pd.DataFrame(columns=["category", "flow_usd", "flow_usd_b"])

    cutoff = _trading_day_cutoff(f, period_days)
    f = f[f["date"] >= cutoff]

    agg = f.groupby("category", as_index=False)["flow_usd"].sum()
    agg["flow_usd_b"] = agg["flow_usd"] / 1e9
    return agg.sort_values("flow_usd", ascending=False).reset_index(drop=True)


def compute_zscore(flows: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """Rolling z-score per ticker, computed only on rows with a valid flow_usd.

    Drops NaN rows before the rolling so `window` reflects actual observations,
    then reindexes back so columns are aligned with the input.
    """
    if flows is None or flows.empty:
        out = flows.copy() if flows is not None else pd.DataFrame()
        for col in ("flow_mean", "flow_std", "flow_z"):
            out[col] = pd.NA
        return out

    f = flows.sort_values(["ticker", "date"]).copy().reset_index(drop=True)

    valid = f.dropna(subset=["flow_usd"]).copy()
    if valid.empty:
        for col in ("flow_mean", "flow_std", "flow_z"):
            f[col] = pd.NA
        return f

    grouped = valid.groupby("ticker")["flow_usd"]
    valid["flow_mean"] = grouped.transform(lambda s: s.rolling(window, min_periods=10).mean())
    valid["flow_std"] = grouped.transform(lambda s: s.rolling(window, min_periods=10).std())
    valid["flow_z"] = (valid["flow_usd"] - valid["flow_mean"]) / valid["flow_std"]

    f = f.merge(
        valid[["ticker", "date", "flow_mean", "flow_std", "flow_z"]],
        on=["ticker", "date"],
        how="left",
    )
    return f


def detect_rotation(flows: pd.DataFrame, short: int = 5, long: int = 20) -> pd.DataFrame:
    """Rotation signal: recent N=short trading-day flow vs the prior (long-short)
    trading-day flow, normalized to comparable window length.

    Columns:
      - flow_short_b: net flow in the last `short` trading days
      - flow_long_b:  net flow in the (long - short) trading days BEFORE that
      - rotation_b:   flow_short - flow_long * short / (long - short)
    """
    cols = ["category", "flow_short_b", "flow_long_b", "rotation_b"]
    if flows is None or flows.empty:
        return pd.DataFrame(columns=cols)

    f = flows.dropna(subset=["date", "flow_usd"]).copy()
    if f.empty:
        return pd.DataFrame(columns=cols)

    trading_dates = sorted(pd.to_datetime(f["date"].unique()))
    if not trading_dates:
        return pd.DataFrame(columns=cols)

    short_n = min(short, len(trading_dates))
    long_n = min(long, len(trading_dates))
    short_start = trading_dates[-short_n]
    long_start = trading_dates[-long_n]

    short_window = f[f["date"] >= short_start]
    long_window = f[(f["date"] >= long_start) & (f["date"] < short_start)]

    fs = short_window.groupby("category")["flow_usd"].sum().rename("flow_short")
    fl = long_window.groupby("category")["flow_usd"].sum().rename("flow_long")
    out = pd.concat([fs, fl], axis=1).fillna(0.0).reset_index()

    denom = (long - short) if (long - short) > 0 else 1
    out["rotation"] = out["flow_short"] - out["flow_long"] * short / denom
    out["flow_short_b"] = out["flow_short"] / 1e9
    out["flow_long_b"] = out["flow_long"] / 1e9
    out["rotation_b"] = out["rotation"] / 1e9
    return out[cols].sort_values("rotation_b", ascending=False).reset_index(drop=True)


def top_movers(flows: pd.DataFrame, n: int = 10, side: str = "both") -> pd.DataFrame:
    if flows is None or flows.empty:
        return flows if flows is not None else pd.DataFrame(columns=_FLOW_COLS)

    f = flows.dropna(subset=["flow_usd", "date"]).copy()
    if f.empty:
        return f

    last_date = f["date"].max()
    today = f[f["date"] == last_date]

    if side == "inflow":
        return today.nlargest(n, "flow_usd")
    if side == "outflow":
        return today.nsmallest(n, "flow_usd")
    return pd.concat(
        [today.nlargest(n, "flow_usd"), today.nsmallest(n, "flow_usd")],
        ignore_index=True,
    )
