"""ETF Flows Tracker — Streamlit entry point."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config.universe import get_tickers
from core.flows_calc import compute_daily_flows, latest_complete_date
from data.cache import HISTORY_FILE, load_history, load_status
from data.price_loader import fetch_prices
from tabs import (
    tab_daily_flows, tab_intraday, tab_morning_brief, tab_quality, tab_rotation, tab_signals,
)

st.set_page_config(page_title="ETF Flows Tracker", page_icon="📊", layout="wide")

st.title("📊 ETF Flows Tracker")
st.caption(
    "Universo de 95 ETFs principales · Flow_t = ΔShares_t × NAV_t con shares oficiales de cada issuer "
    "(SPDR, iShares, ProShares y otros), fechadas por sesión de trading."
)
st.info(
    "**Datos reconstruidos el 2026-10-05.** El histórico anterior (may–oct 2026) venía de yfinance, cuyas shares "
    "de ETFs estaban congeladas, y de cambios entre fuentes que generaban flows falsos; se descartó. "
    "SPDR y ProShares traen historial oficial desde sep-2025; iShares acumula desde oct-2026.",
    icon="ℹ️",
)


def _history_version() -> float:
    return HISTORY_FILE.stat().st_mtime if HISTORY_FILE.exists() else 0.0


@st.cache_data(ttl=3600)
def load_flows(version: float) -> pd.DataFrame:
    """`version` = history file mtime, so a new snapshot invalidates the cache immediately."""
    history = load_history()
    if history.empty:
        return pd.DataFrame()
    tickers = sorted(history["ticker"].dropna().unique().tolist())
    prices = fetch_prices(tickers, start=history["as_of_date"].min() - pd.Timedelta(days=7))
    return compute_daily_flows(history, prices)


history = load_history()
status = load_status()
flows = load_flows(_history_version())

with st.sidebar:
    st.header("Estado")
    complete = latest_complete_date(flows) if not flows.empty else None
    if complete is not None:
        st.success(f"Última sesión completa: {complete.date()}")
        newest = flows["date"].max()
        if newest > complete:
            st.caption(f"Sesión {newest.date()} con cobertura parcial (issuers que aún no publican).")
    else:
        st.error("Sin datos aún. Dispara el workflow *Daily ETF Snapshot* en GitHub Actions.")

    n_total = len(get_tickers())
    if not status.empty:
        ok = int((status["status"] == "ok").sum())
        st.metric("Cobertura con fuente oficial", f"{ok / n_total:.0%}", f"{ok}/{n_total} ETFs")
        failing = status[status["status"].isin(["error", "rejected"])]
        if not failing.empty:
            st.warning(f"{len(failing)} fuentes fallaron en la última corrida: {', '.join(failing['ticker'])}")
        st.caption("Detalle por ETF en la pestaña 🩺 Calidad de datos.")

    if st.button("🔄 Refrescar caché"):
        st.cache_data.clear()
        st.rerun()

tabs = st.tabs([
    "📥📤 Daily Flows",
    "⏱️ Intraday Pressure",
    "🔄 Rotation Map",
    "⚡ Signals",
    "📰 Morning Brief",
    "🩺 Calidad de datos",
])

with tabs[0]:
    tab_daily_flows.render(flows)
with tabs[1]:
    tab_intraday.render()
with tabs[2]:
    tab_rotation.render(flows)
with tabs[3]:
    tab_signals.render(flows)
with tabs[4]:
    tab_morning_brief.render(flows)
with tabs[5]:
    tab_quality.render(flows, history, status)
