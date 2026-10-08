"""Sector-level flow analytics: GICS sector aggregation, streaks, anomalies, flow vs. return."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config.universe import SECTOR_BENCHMARK, SECTOR_ES, get_universe, sector_of
from core.flows_calc import sessions_up_to

WINDOWS = (1, 5, 20, 60)


def with_sector(flows: pd.DataFrame) -> pd.DataFrame:
    """Valid flows of sector/industry ETFs, tagged with their GICS sector."""
    if flows is None or flows.empty:
        return pd.DataFrame()
    v = flows.dropna(subset=["flow_usd"]).copy()
    v["sector"] = v["ticker"].map(sector_of)
    return v.dropna(subset=["sector"])


def sector_daily(sf: pd.DataFrame) -> pd.DataFrame:
    """date × sector net flow ($) and flow as % of the sector's previous-day AUM."""
    g = sf.groupby(["date", "sector"]).agg(flow_usd=("flow_usd", "sum"), aum_prev=("aum_prev", "sum")).reset_index()
    g["flow_pct"] = g["flow_usd"] / g["aum_prev"]
    return g


def _streak(values: pd.Series) -> int:
    """+n = n consecutive inflow sessions ending at the last one, −n = outflows."""
    vals = [v for v in values.tolist() if pd.notna(v)]
    if not vals or vals[-1] == 0:
        return 0
    sign = np.sign(vals[-1])
    n = 0
    for v in reversed(vals):
        if np.sign(v) != sign:
            break
        n += 1
    return int(sign * n)


def _zscore_last(series: pd.Series, lookback: int = 60, min_obs: int = 10) -> float:
    """z of the last value vs. the previous `lookback` values (the last one excluded)."""
    s = series.dropna()
    if len(s) < min_obs + 1:
        return float("nan")
    hist = s.iloc[-(lookback + 1):-1]
    sd = hist.std()
    return float((s.iloc[-1] - hist.mean()) / sd) if sd and sd > 0 else float("nan")


def _returns(flows: pd.DataFrame, ticker: str, session, n: int) -> float:
    """Price return of `ticker` over the last n sessions ending at `session` (split-adjusted close)."""
    d = flows[(flows["ticker"] == ticker) & (flows["date"] <= pd.Timestamp(session))].dropna(subset=["close"])
    d = d.sort_values("date").tail(n + 1)
    if len(d) < n + 1:
        return float("nan")
    return float(d["close"].iloc[-1] / d["close"].iloc[0] - 1)


def sector_panel(flows: pd.DataFrame, session) -> pd.DataFrame:
    """One row per GICS sector: windowed flows, % AUM, z, streak, persistence, sparkline, returns."""
    sf = with_sector(flows)
    if sf.empty or session is None:
        return pd.DataFrame()
    daily = sector_daily(sf[sf["date"] <= pd.Timestamp(session)])
    rows = []
    for sector in SECTOR_BENCHMARK:
        d = daily[daily["sector"] == sector].sort_values("date")
        if d.empty:
            continue
        row = {"sector": sector, "sector_es": SECTOR_ES[sector], "benchmark": SECTOR_BENCHMARK[sector]}
        for n in WINDOWS:
            dates = sessions_up_to(daily, session, n)
            w = d[d["date"].isin(dates)]
            row[f"flow_{n}D"] = w["flow_usd"].sum() if not w.empty else np.nan
            row[f"pct_{n}D"] = row[f"flow_{n}D"] / w["aum_prev"].iloc[0] if not w.empty and w["aum_prev"].iloc[0] else np.nan
            row[f"ret_{n}D"] = _returns(flows, SECTOR_BENCHMARK[sector], session, n)
        row["has_session"] = bool((d["date"] == pd.Timestamp(session)).any())
        row["z"] = _zscore_last(d["flow_pct"]) if row["has_session"] else np.nan
        row["streak"] = _streak(d["flow_usd"])
        last20 = d.tail(20)["flow_usd"]
        row["inflow_share_20"] = float((last20 > 0).mean()) if len(last20) else np.nan
        row["spark"] = (last20 / 1e6).round(1).tolist()
        aum = sf[(sf["sector"] == sector) & (sf["date"] == d["date"].max())]["aum"].sum()
        row["aum"] = aum
        rows.append(row)
    return pd.DataFrame(rows)


def industry_panel(flows: pd.DataFrame, session, n: int = 20) -> pd.DataFrame:
    """Per sector/industry ETF: flow over the session and over n sessions, % AUM, z, n-session return."""
    sf = with_sector(flows)
    sf = sf[sf["date"] <= pd.Timestamp(session)] if session is not None else sf
    if sf.empty:
        return pd.DataFrame()
    uni = get_universe()
    dates_n = sessions_up_to(sf, session, n)
    rows = []
    for t, d in sf.groupby("ticker"):
        d = d.sort_values("date")
        w = d[d["date"].isin(dates_n)]
        today = d[d["date"] == pd.Timestamp(session)]
        rows.append({
            "ticker": t, "sector": d["sector"].iloc[0], "sector_es": SECTOR_ES[d["sector"].iloc[0]],
            "industry": uni[t]["subcategory"], "is_benchmark": t in SECTOR_BENCHMARK.values(),
            "flow_1D": today["flow_usd"].sum() if not today.empty else np.nan,
            "pct_1D": today["flow_pct_aum"].iloc[0] if not today.empty else np.nan,
            f"flow_{n}D": w["flow_usd"].sum() if not w.empty else np.nan,
            f"pct_{n}D": w["flow_usd"].sum() / w["aum_prev"].iloc[0] if not w.empty and w["aum_prev"].iloc[0] else np.nan,
            "z": _zscore_last(d["flow_pct_aum"]) if not today.empty else np.nan,
            "streak": _streak(d["flow_usd"]),
            f"ret_{n}D": _returns(flows, t, session, n),
            "aum": d["aum"].iloc[-1],
        })
    return pd.DataFrame(rows)


def _usd(x: float) -> str:
    sign = "+" if x > 0 else "-" if x < 0 else ""
    a = abs(x)
    return f"{sign}${a / 1e9:.2f}B" if a >= 1e9 else f"{sign}${a / 1e6:.0f}M"


def daily_reading(panel: pd.DataFrame, industries: pd.DataFrame) -> list[str]:
    """Factual one-liners for the session, built only from the numbers (no model, no opinion)."""
    out: list[str] = []
    p = panel[panel["has_session"]].dropna(subset=["flow_1D"])
    if p.empty:
        return out
    ins = p[p["flow_1D"] > 0].nlargest(2, "flow_1D")
    outs = p[p["flow_1D"] < 0].nsmallest(2, "flow_1D")
    if not ins.empty:
        out.append("**Entradas:** " + ", ".join(
            f"{r.sector_es} {_usd(r.flow_1D)} ({r.pct_1D * 100:+.2f}% AUM)" for r in ins.itertuples()))
    if not outs.empty:
        out.append("**Salidas:** " + ", ".join(
            f"{r.sector_es} {_usd(r.flow_1D)} ({r.pct_1D * 100:+.2f}% AUM)" for r in outs.itertuples()))
    streaks = p[p["streak"].abs() >= 3].sort_values("streak", key=abs, ascending=False).head(2)
    for r in streaks.itertuples():
        side = "entradas" if r.streak > 0 else "salidas"
        out.append(f"**Racha:** {r.sector_es} suma {abs(r.streak)} sesiones seguidas con {side} "
                   f"({_usd(r.flow_5D)} en 5 sesiones).")
    turns = p[(np.sign(p["flow_1D"]) != np.sign(p["flow_20D"])) & (p["z"].abs() >= 1.5)]
    for r in turns.head(1).itertuples():
        out.append(f"**Giro:** {r.sector_es} {'recibe entradas' if r.flow_1D > 0 else 'registra salidas'} "
                   f"({_usd(r.flow_1D)}, z {r.z:+.1f}) contra {_usd(r.flow_20D)} acumulado en 20 sesiones.")
    if not industries.empty:
        hot = industries.dropna(subset=["z"])
        hot = hot[(hot["z"].abs() >= 2) & ~hot["is_benchmark"]].sort_values("z", key=abs, ascending=False).head(2)
        for r in hot.itertuples():
            out.append(f"**Industria inusual:** {r.ticker} ({r.industry}) {_usd(r.flow_1D)} "
                       f"({r.pct_1D * 100:+.2f}% AUM, z {r.z:+.1f}).")
    return out


MIN_SECTORS = 9


def sector_session(flows: pd.DataFrame, session) -> pd.Timestamp | None:
    """Latest session <= `session` where at least MIN_SECTORS Select Sector SPDRs have a flow.

    SPDR publishes a day after iShares, so the newest date often has only the
    iShares sector funds; ranking sectors on it would compare 3 sectors, not 11.
    """
    if flows is None or flows.empty or session is None:
        return None
    v = flows.dropna(subset=["flow_usd"])
    v = v[v["ticker"].isin(SECTOR_BENCHMARK.values()) & (v["date"] <= pd.Timestamp(session))]
    counts = v.groupby("date")["ticker"].nunique()
    ok = counts[counts >= MIN_SECTORS]
    return pd.Timestamp(ok.index.max()) if not ok.empty else None
