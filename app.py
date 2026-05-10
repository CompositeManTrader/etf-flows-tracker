"""ETF Flows Tracker — Streamlit entry point."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config.universe import get_tickers
from core.flows_calc import compute_daily_flows
from data.cache import latest_snapshot_date, load_history
from data.price_loader import check_coverage, fetch_prices
from tabs import tab_daily_flows, tab_intraday, tab_morning_brief, tab_rotation, tab_signals

st.set_page_config(page_title="ETF Flows Tracker", page_icon="📊", layout="wide")

st.title("📊 ETF Flows Tracker")
st.caption(
    "Universo de ~95 ETFs principales (US broad/sectores/factor, intl, EM, bonds, commodities, REITs, crypto). "
    "v1: yfinance + snapshot diario · Flow_t = ΔShares × Close_t."
)


@st.cache_data(ttl=3600)
def load_flows() -> pd.DataFrame:
    history = load_history()
    if history.empty:
        return pd.DataFrame()
    tickers = sorted(history["ticker"].dropna().unique().tolist())
    if not tickers:
        return pd.DataFrame()
    prices = fetch_prices(tickers, period="120d")
    return compute_daily_flows(history, prices)


# Sidebar
with st.sidebar:
    st.header("Estado")
    last = latest_snapshot_date()
    if last is not None:
        st.success(f"Último snapshot: {pd.Timestamp(last).date()}")
    else:
        st.error(
            "No hay snapshots aún.\n\n"
            "Corre `python jobs/daily_snapshot.py` o dispara el workflow de GitHub Actions."
        )

    history = load_history()
    if not history.empty and last is not None:
        last_snap = history[history["snapshot_date"] == last]
        cov = check_coverage(last_snap)
        st.metric("Cobertura yfinance", f"{cov['coverage_pct']:.1f}%", f"{cov['covered']}/{cov['total']}")
        if cov["missing"]:
            with st.expander(f"Tickers sin cobertura ({len(cov['missing'])})"):
                st.write(", ".join(cov["missing"]))
    else:
        st.metric("Universo", f"{len(get_tickers())} ETFs")

    if st.button("🔄 Refrescar caché"):
        st.cache_data.clear()
        st.rerun()


# Tabs
flows = load_flows()

tabs = st.tabs([
    "📥📤 Daily Flows",
    "⏱️ Intraday Pressure",
    "🔄 Rotation Map",
    "⚡ Signals",
    "📰 Morning Brief",
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
