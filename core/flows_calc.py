"""Core flow calculations: deltas × close, aggregations, z-scores, rotation."""
from __future__ import annotations

import pandas as pd

from config.universe import get_universe

_FLOW_COLS = [
    "date", "ticker", "name", "category", "subcategory", "issuer",
    "shares_outstanding", "prev_shares", "delta_shares", "close", "volume", "flow_usd",
]


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    universe = get_universe()
    meta = pd.DataFrame.from_dict(universe, orient="index").reset_index().rename(columns={"index": "ticker"})
    return df.merge(meta, on="ticker", how="left")


def compute_daily_flows(shares_history: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    if shares_history is None or shares_history.empty:
        return pd.DataFrame(columns=_FLOW_COLS)

    h = shares_history.copy()
    h["snapshot_date"] = pd.to_datetime(h["snapshot_date"]).dt.normalize()
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
        p["date"] = pd.to_datetime(p["date"]).dt.normalize()
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


def aggregate_by_category(flows: pd.DataFrame, period_days: int = 1) -> pd.DataFrame:
    if flows is None or flows.empty:
        return pd.DataFrame(columns=["category", "flow_usd", "flow_usd_b"])

    f = flows.dropna(subset=["date", "flow_usd"]).copy()
    if f.empty:
        return pd.DataFrame(columns=["category", "flow_usd", "flow_usd_b"])

    max_date = f["date"].max()
    cutoff = max_date - pd.Timedelta(days=period_days - 1)
    f = f[f["date"] >= cutoff]

    agg = f.groupby("category", as_index=False)["flow_usd"].sum()
    agg["flow_usd_b"] = agg["flow_usd"] / 1e9
    return agg.sort_values("flow_usd", ascending=False).reset_index(drop=True)


def compute_zscore(flows: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    if flows is None or flows.empty:
        out = flows.copy() if flows is not None else pd.DataFrame()
        for col in ("flow_mean", "flow_std", "flow_z"):
            out[col] = pd.NA
        return out

    f = flows.sort_values(["ticker", "date"]).copy()
    grouped = f.groupby("ticker")["flow_usd"]
    f["flow_mean"] = grouped.transform(lambda s: s.rolling(window, min_periods=10).mean())
    f["flow_std"] = grouped.transform(lambda s: s.rolling(window, min_periods=10).std())
    f["flow_z"] = (f["flow_usd"] - f["flow_mean"]) / f["flow_std"]
    return f


def detect_rotation(flows: pd.DataFrame, short: int = 5, long: int = 20) -> pd.DataFrame:
    cols = ["category", "flow_short_b", "flow_long_b", "rotation_b"]
    if flows is None or flows.empty:
        return pd.DataFrame(columns=cols)

    f = flows.dropna(subset=["date", "flow_usd"]).copy()
    if f.empty:
        return pd.DataFrame(columns=cols)

    max_date = f["date"].max()
    short_start = max_date - pd.Timedelta(days=short - 1)
    long_start = max_date - pd.Timedelta(days=long - 1)

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
