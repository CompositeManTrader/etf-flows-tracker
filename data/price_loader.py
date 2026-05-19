"""yfinance loaders: shares outstanding, daily prices, intraday quotes."""
from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

from config.universe import get_tickers


def _utc_now_naive() -> pd.Timestamp:
    """Replacement for deprecated pd.Timestamp.utcnow()."""
    return pd.Timestamp.now(tz="UTC").tz_localize(None)


def _safe_get(obj, attr: str, default=None):
    try:
        return getattr(obj, attr, default)
    except Exception:  # noqa: BLE001
        return default


def _last_shares_full(ticker_obj: yf.Ticker) -> float | None:
    """Try Ticker.get_shares_full() and return the most recent value if any."""
    try:
        end = pd.Timestamp.utcnow().normalize()
        start = end - pd.Timedelta(days=30)
        series = ticker_obj.get_shares_full(start=start, end=end)
    except Exception:  # noqa: BLE001
        return None
    if series is None or (hasattr(series, "empty") and series.empty):
        return None
    try:
        # series is indexed by datetime; take last non-null
        return float(series.dropna().iloc[-1])
    except Exception:  # noqa: BLE001
        return None


def fetch_shares_outstanding(tickers: list[str] | None = None, sleep: float = 0.15) -> pd.DataFrame:
    """Fetch shares outstanding with a layered fallback chain:

    1. Ticker.info["sharesOutstanding"]
    2. Ticker.info["impliedSharesOutstanding"]
    3. Ticker.fast_info.shares  (different endpoint, often works when .info fails)
    4. Last value of Ticker.get_shares_full() over the last 30 days (historical)
    """
    if tickers is None:
        tickers = get_tickers()

    rows = []
    fetched_at = _utc_now_naive()
    for t in tickers:
        shares: float | None = None
        source = "missing"
        try:
            t_obj = yf.Ticker(t)
            try:
                info = t_obj.info or {}
            except Exception:  # noqa: BLE001
                info = {}
            shares = info.get("sharesOutstanding")
            if shares is not None:
                source = "info.sharesOutstanding"
            if shares is None:
                shares = info.get("impliedSharesOutstanding")
                if shares is not None:
                    source = "info.impliedSharesOutstanding"
            if shares is None:
                fi = _safe_get(t_obj, "fast_info")
                if fi is not None:
                    fi_shares = _safe_get(fi, "shares")
                    if fi_shares is not None and pd.notna(fi_shares):
                        shares = float(fi_shares)
                        source = "fast_info.shares"
            if shares is None:
                hist = _last_shares_full(t_obj)
                if hist is not None:
                    shares = hist
                    source = "get_shares_full"
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
    period: str = "120d",
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch raw (unadjusted) close prices for flow calculation.

    auto_adjust=False is critical: Flow_t = ΔShares × Close_t needs the actual
    market close on day t, not the dividend-back-adjusted close.
    """
    if tickers is None:
        tickers = get_tickers()

    raw = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=False,
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
    tz = getattr(out["date"].dt, "tz", None)
    if tz is not None:
        try:
            out["date"] = out["date"].dt.tz_convert(None)
        except (TypeError, AttributeError):
            try:
                out["date"] = out["date"].dt.tz_localize(None)
            except (TypeError, AttributeError):
                pass
    return out


def fetch_intraday_quote(tickers: list[str] | None = None) -> pd.DataFrame:
    """Last-session quote + ADV20 + relative volume.

    Note: with interval='1d', last_session_volume is the most recent COMPLETED
    trading session (yesterday if pre-market, today if post-close), not a true
    intraday read.
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
        if grp.empty:
            continue
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
