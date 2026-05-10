"""yfinance loaders: shares outstanding, daily prices, intraday quotes."""
from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

from config.universe import get_tickers


def fetch_shares_outstanding(tickers: list[str] | None = None, sleep: float = 0.15) -> pd.DataFrame:
    if tickers is None:
        tickers = get_tickers()

    rows = []
    fetched_at = pd.Timestamp.utcnow()
    for t in tickers:
        shares = None
        source = "yfinance"
        try:
            info = yf.Ticker(t).info or {}
            shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
            if shares is None:
                source = "missing"
        except Exception as e:  # noqa: BLE001
            source = f"error: {type(e).__name__}: {e}"
        rows.append({
            "ticker": t,
            "shares_outstanding": shares,
            "fetched_at": fetched_at,
            "source": source,
        })
        time.sleep(sleep)

    return pd.DataFrame(rows)


def fetch_prices(
    tickers: list[str] | None = None,
    period: str = "60d",
    interval: str = "1d",
) -> pd.DataFrame:
    if tickers is None:
        tickers = get_tickers()

    raw = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=True,
        progress=False,
        threads=True,
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
        # single ticker case
        sub = raw[["Close", "Volume"]].copy()
        sub = sub.dropna(how="all").reset_index().rename(
            columns={"Date": "date", "Close": "close", "Volume": "volume"}
        )
        sub["ticker"] = tickers[0]
        frames.append(sub[["date", "ticker", "close", "volume"]])

    if not frames:
        return pd.DataFrame(columns=["date", "ticker", "close", "volume"])

    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"])
    if hasattr(out["date"].dt, "tz_localize"):
        try:
            out["date"] = out["date"].dt.tz_localize(None)
        except (TypeError, AttributeError):
            pass
    return out


def fetch_intraday_quote(tickers: list[str] | None = None) -> pd.DataFrame:
    if tickers is None:
        tickers = get_tickers()

    prices = fetch_prices(tickers, period="30d")
    as_of = pd.Timestamp.utcnow()

    if prices.empty:
        return pd.DataFrame(
            columns=["ticker", "last_price", "today_volume", "adv20", "rel_volume", "as_of"]
        )

    rows = []
    for t, grp in prices.groupby("ticker"):
        grp = grp.sort_values("date")
        if grp.empty:
            continue
        last = grp.iloc[-1]
        adv20 = grp["volume"].tail(20).mean()
        last_vol = float(last["volume"]) if pd.notna(last["volume"]) else None
        rel = (last_vol / adv20) if (adv20 and last_vol) else None
        rows.append({
            "ticker": t,
            "last_price": float(last["close"]) if pd.notna(last["close"]) else None,
            "today_volume": last_vol,
            "adv20": float(adv20) if pd.notna(adv20) else None,
            "rel_volume": float(rel) if rel is not None else None,
            "as_of": as_of,
        })

    return pd.DataFrame(rows)


def check_coverage(df_shares: pd.DataFrame) -> dict:
    total = len(df_shares)
    missing_mask = df_shares["shares_outstanding"].isna()
    covered = int((~missing_mask).sum())
    missing = df_shares.loc[missing_mask, "ticker"].tolist()
    pct = (covered / total * 100) if total else 0.0
    return {
        "total": total,
        "covered": covered,
        "coverage_pct": pct,
        "missing": missing,
    }
