"""yfinance loaders: daily prices and intraday quotes.

yfinance is NOT used for shares outstanding: its ETF values are frozen for
months (see data/sources for the official issuer feeds).
"""
from __future__ import annotations

import pandas as pd
import yfinance as yf

from config.universe import get_tickers


def _utc_now_naive() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC").tz_localize(None)


def fetch_prices(
    tickers: list[str] | None = None,
    period: str = "120d",
    interval: str = "1d",
    start: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Raw (unadjusted) daily close + volume. Pass `start` to override `period`."""
    if tickers is None:
        tickers = get_tickers()

    kwargs = {"start": pd.Timestamp(start).strftime("%Y-%m-%d")} if start is not None else {"period": period}
    raw = yf.download(
        tickers=tickers,
        interval=interval,
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True,
        **kwargs,
    )

    if raw is None or raw.empty:
        return pd.DataFrame(columns=["date", "ticker", "close", "volume"])

    frames: list[pd.DataFrame] = []
    if isinstance(raw.columns, pd.MultiIndex):
        for t in tickers:
            try:
                sub = raw[t][["Close", "Volume"]].copy()
            except (KeyError, TypeError):
                continue
            sub = sub.dropna(how="all")
            if sub.empty:
                continue
            sub = sub.reset_index().rename(columns={"Date": "date", "Close": "close", "Volume": "volume"})
            sub["ticker"] = t
            frames.append(sub[["date", "ticker", "close", "volume"]])
    else:
        sub = raw[["Close", "Volume"]].dropna(how="all").reset_index().rename(
            columns={"Date": "date", "Close": "close", "Volume": "volume"}
        )
        sub["ticker"] = tickers[0]
        frames.append(sub[["date", "ticker", "close", "volume"]])

    if not frames:
        return pd.DataFrame(columns=["date", "ticker", "close", "volume"])

    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"])
    if getattr(out["date"].dt, "tz", None) is not None:
        out["date"] = out["date"].dt.tz_convert(None)
    return out


def fetch_intraday_quote(tickers: list[str] | None = None) -> pd.DataFrame:
    """Last-session quote + ADV20 + relative volume.

    With interval='1d', last_session_volume is the most recent COMPLETED
    trading session, not a true intraday read.
    """
    if tickers is None:
        tickers = get_tickers()

    prices = fetch_prices(tickers, period="30d")
    as_of = _utc_now_naive()

    if prices.empty:
        return pd.DataFrame(
            columns=["ticker", "last_price", "last_session_volume", "adv20", "rel_volume", "as_of"]
        )

    rows = []
    for t, grp in prices.groupby("ticker"):
        grp = grp.sort_values("date")
        last = grp.iloc[-1]
        adv20 = grp["volume"].tail(20).mean()
        last_vol = float(last["volume"]) if pd.notna(last["volume"]) else None
        rel = (last_vol / adv20) if (adv20 and last_vol) else None
        rows.append({
            "ticker": t,
            "last_price": float(last["close"]) if pd.notna(last["close"]) else None,
            "last_session_volume": last_vol,
            "adv20": float(adv20) if pd.notna(adv20) else None,
            "rel_volume": float(rel) if rel is not None else None,
            "as_of": as_of,
        })

    return pd.DataFrame(rows)
