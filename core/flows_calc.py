"""Core flow calculations: ΔShares × NAV with data-quality gates, aggregations, z-scores, rotation."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config.universe import get_universe
from core.trading_calendar import NYSE_HOLIDAYS

JUMP_THRESHOLD = 0.15   # one-session |Δshares / shares| above this needs confirmation
CONFIRM_TOL = 0.02      # spike removal: neighbours this close mean the middle print was bad
SPLIT_TOL = 0.05        # shares×price roughly unchanged across a big jump => split
VALID_QUALITY = ("ok", "multi_day")

_FLOW_COLS = [
    "date", "ticker", "name", "category", "subcategory", "issuer", "source",
    "shares_outstanding", "prev_shares", "delta_shares", "nav", "close", "price", "price_basis",
    "volume", "aum", "flow_usd", "flow_pct_aum", "gap_days", "quality", "as_of_inferred",
]
_HOLIDAYS = np.array(sorted(NYSE_HOLIDAYS), dtype="datetime64[D]")


def _to_naive_date(series: pd.Series) -> pd.Series:
    s = pd.to_datetime(series, errors="coerce")
    if getattr(s.dt, "tz", None) is not None:
        s = s.dt.tz_convert(None)
    return s.dt.normalize()


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    meta = pd.DataFrame.from_dict(get_universe(), orient="index").reset_index().rename(columns={"index": "ticker"})
    return df.merge(meta, on="ticker", how="left")


def _drop_spikes(h: pd.DataFrame) -> pd.DataFrame:
    """Remove isolated bad prints: a value far from BOTH neighbours while the neighbours agree."""
    s = h.groupby("ticker")["shares_outstanding"]
    prev, nxt, cur = s.shift(1), s.shift(-1), h["shares_outstanding"]
    spike = (
        ((cur / prev - 1).abs() > JUMP_THRESHOLD)
        & ((cur / nxt - 1).abs() > JUMP_THRESHOLD)
        & ((nxt / prev - 1).abs() < CONFIRM_TOL)
    )
    return h[~spike.fillna(False)]


def _trading_gap(prev: pd.Series, curr: pd.Series) -> np.ndarray:
    """Trading sessions in (prev, curr]; 0 where prev is missing."""
    ok = prev.notna() & curr.notna()
    out = np.zeros(len(prev), dtype=int)
    if ok.any():
        p = prev[ok].values.astype("datetime64[D]") + np.timedelta64(1, "D")
        c = curr[ok].values.astype("datetime64[D]") + np.timedelta64(1, "D")
        out[ok.values] = np.busday_count(p, c, holidays=_HOLIDAYS)
    return out


def compute_daily_flows(shares_history: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Flow_t = (S_t − S_{t−1}) × NAV_t, per trading session reported by the issuer.

    Close is used only when the source publishes no NAV. Each row carries a
    `quality` label; flow_usd is NaN unless quality is ok / multi_day:
      first     — first observation, no previous level
      split     — big share jump offset by the price move (split / reverse split)
      pending   — big jump on the latest print, waits for the next print to confirm
      suspect   — big jump that the next print does not confirm
      no_price  — neither NAV nor close for that session
      multi_day — previous print is >1 session back; flow covers the whole gap
    """
    if shares_history is None or shares_history.empty:
        return pd.DataFrame(columns=_FLOW_COLS)

    h = shares_history.copy()
    h["date"] = _to_naive_date(h["as_of_date"])
    h = h.dropna(subset=["date", "shares_outstanding"]).sort_values(["ticker", "date"])
    h = _drop_spikes(h)

    if prices is not None and not prices.empty:
        p = prices.copy()
        p["date"] = _to_naive_date(p["date"])
        h = h.merge(p[["date", "ticker", "close", "volume"]], on=["date", "ticker"], how="left")
    else:
        h["close"], h["volume"] = np.nan, np.nan
    h = h.sort_values(["ticker", "date"]).reset_index(drop=True)

    h["nav"] = pd.to_numeric(h.get("nav"), errors="coerce")
    h["close"] = pd.to_numeric(h["close"], errors="coerce")
    h["price"] = h["nav"].fillna(h["close"])
    h["price_basis"] = np.where(h["nav"].notna(), "nav", np.where(h["close"].notna(), "close", None))

    g = h.groupby("ticker")
    h["prev_shares"] = g["shares_outstanding"].shift(1)
    h["next_shares"] = g["shares_outstanding"].shift(-1)
    h["prev_price"] = g["price"].shift(1)
    h["prev_date"] = g["date"].shift(1)
    h["delta_shares"] = h["shares_outstanding"] - h["prev_shares"]
    h["gap_days"] = _trading_gap(h["prev_date"], h["date"])

    ratio = h["shares_outstanding"] / h["prev_shares"]
    big = (ratio - 1).abs() > JUMP_THRESHOLD
    split = big & ((ratio * h["price"] / h["prev_price"] - 1).abs() < SPLIT_TOL)
    # A real big creation/redemption sticks: the next print stays nearer the new level than the old one.
    confirmed = (h["next_shares"] - h["shares_outstanding"]).abs() < (h["next_shares"] - h["prev_shares"]).abs()

    h["quality"] = np.select(
        [h["prev_shares"].isna(), split, big & h["next_shares"].isna(), big & ~confirmed,
         h["price"].isna(), h["gap_days"] > 1],
        ["first", "split", "pending", "suspect", "no_price", "multi_day"],
        default="ok",
    )

    valid = h["quality"].isin(VALID_QUALITY)
    h["flow_usd"] = (h["delta_shares"] * h["price"]).where(valid)
    h["aum"] = h["shares_outstanding"] * h["price"]
    h["flow_pct_aum"] = h["flow_usd"] / (h["prev_shares"] * h["prev_price"])
    if "as_of_inferred" not in h:
        h["as_of_inferred"] = False

    h = _enrich(h)
    return h[_FLOW_COLS].sort_values(["date", "ticker"]).reset_index(drop=True)


def session_coverage(flows: pd.DataFrame) -> pd.Series:
    """Tickers with a valid flow per session."""
    v = flows.dropna(subset=["flow_usd"])
    return v.groupby("date")["ticker"].nunique().sort_index()


def latest_complete_date(flows: pd.DataFrame, min_ratio: float = 0.6) -> pd.Timestamp | None:
    """Most recent session where at least `min_ratio` of the recently-reporting tickers have a flow.

    Issuers publish with different lags (e.g. SPDR a day after iShares), so the
    newest date often holds only a handful of tickers; ranking that day would
    make two or three funds look like the whole market.
    """
    cov = session_coverage(flows)
    if cov.empty:
        return None
    target = cov.tail(10).max() * min_ratio
    complete = cov[cov >= target]
    return pd.Timestamp(complete.index.max() if not complete.empty else cov.index.max())


def _trading_day_cutoff(f: pd.DataFrame, n_days: int) -> pd.Timestamp:
    """Date that, used as `date >= cutoff`, keeps the last N trading days present in `f`."""
    trading_dates = sorted(pd.to_datetime(f["date"].dropna().unique()))
    if not trading_dates:
        return pd.Timestamp.min
    return pd.Timestamp(trading_dates[max(0, len(trading_dates) - n_days)])


def aggregate_by_category(flows: pd.DataFrame, period_days: int = 1) -> pd.DataFrame:
    if flows is None or flows.empty:
        return pd.DataFrame(columns=["category", "flow_usd", "flow_usd_b"])

    f = flows.dropna(subset=["date", "flow_usd"]).copy()
    if f.empty:
        return pd.DataFrame(columns=["category", "flow_usd", "flow_usd_b"])

    f = f[f["date"] <= latest_complete_date(f)]
    f = f[f["date"] >= _trading_day_cutoff(f, period_days)]
    agg = f.groupby("category", as_index=False)["flow_usd"].sum()
    agg["flow_usd_b"] = agg["flow_usd"] / 1e9
    return agg.sort_values("flow_usd", ascending=False).reset_index(drop=True)


def compute_zscore(flows: pd.DataFrame, window: int = 60, value_col: str = "flow_pct_aum") -> pd.DataFrame:
    """Rolling z-score per ticker on valid observations only.

    Defaults to flow as % of AUM so a $500M print in SPY and in a $2B ETF are
    not treated as the same event.
    """
    if flows is None or flows.empty:
        out = flows.copy() if flows is not None else pd.DataFrame()
        for col in ("flow_mean", "flow_std", "flow_z"):
            out[col] = pd.NA
        return out

    f = flows.sort_values(["ticker", "date"]).reset_index(drop=True)
    valid = f.dropna(subset=[value_col]).copy()
    if valid.empty:
        for col in ("flow_mean", "flow_std", "flow_z"):
            f[col] = pd.NA
        return f

    grouped = valid.groupby("ticker")[value_col]
    valid["flow_mean"] = grouped.transform(lambda s: s.rolling(window, min_periods=10).mean())
    valid["flow_std"] = grouped.transform(lambda s: s.rolling(window, min_periods=10).std())
    valid["flow_z"] = (valid[value_col] - valid["flow_mean"]) / valid["flow_std"]

    return f.merge(valid[["ticker", "date", "flow_mean", "flow_std", "flow_z"]], on=["ticker", "date"], how="left")


def detect_rotation(flows: pd.DataFrame, short: int = 5, long: int = 20) -> pd.DataFrame:
    """Recent `short`-session flow vs the prior (long − short) sessions, normalized to equal length.

    flow_short_b: last `short` sessions · flow_long_b: the (long − short) sessions before those ·
    rotation_b = flow_short − flow_long × short / (long − short)
    """
    cols = ["category", "flow_short_b", "flow_long_b", "rotation_b"]
    if flows is None or flows.empty:
        return pd.DataFrame(columns=cols)

    f = flows.dropna(subset=["date", "flow_usd"]).copy()
    if f.empty:
        return pd.DataFrame(columns=cols)

    f = f[f["date"] <= latest_complete_date(f)]
    trading_dates = sorted(pd.to_datetime(f["date"].unique()))
    short_start = trading_dates[-min(short, len(trading_dates))]
    long_start = trading_dates[-min(long, len(trading_dates))]

    fs = f[f["date"] >= short_start].groupby("category")["flow_usd"].sum().rename("flow_short")
    fl = f[(f["date"] >= long_start) & (f["date"] < short_start)].groupby("category")["flow_usd"].sum().rename("flow_long")
    out = pd.concat([fs, fl], axis=1).fillna(0.0).reset_index()

    denom = (long - short) if (long - short) > 0 else 1
    out["rotation"] = out["flow_short"] - out["flow_long"] * short / denom
    out["flow_short_b"] = out["flow_short"] / 1e9
    out["flow_long_b"] = out["flow_long"] / 1e9
    out["rotation_b"] = out["rotation"] / 1e9
    return out[cols].sort_values("rotation_b", ascending=False).reset_index(drop=True)


def top_movers(flows: pd.DataFrame, n: int = 10, side: str = "both", date=None) -> pd.DataFrame:
    if flows is None or flows.empty:
        return flows if flows is not None else pd.DataFrame(columns=_FLOW_COLS)

    f = flows.dropna(subset=["flow_usd", "date"])
    if f.empty:
        return f

    date = pd.Timestamp(date) if date is not None else latest_complete_date(f)
    today = f[f["date"] == date]
    if side == "inflow":
        return today.nlargest(n, "flow_usd")
    if side == "outflow":
        return today.nsmallest(n, "flow_usd")
    both = pd.concat([today.nlargest(n, "flow_usd"), today.nsmallest(n, "flow_usd")], ignore_index=True)
    return both.drop_duplicates(subset="ticker")
