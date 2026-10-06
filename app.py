"""ETF Flows Tracker — Streamlit entry point: data loading, global controls and navigation."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config.universe import get_categories, get_tickers
from core.flows_calc import compute_daily_flows, compute_monthly_flows, latest_complete_date, session_coverage
from data.cache import HISTORY_FILE, MONTHLY_FILE, load_history, load_monthly, load_status
from data.price_loader import fetch_prices
from ui import theme
from views import (
    Ctx, etf_detail, methodology, overview, quality, rotation, signals, vanguard_monthly, volume,
)

st.set_page_config(page_title="ETF Flows Tracker", page_icon=":material/monitoring:", layout="wide")
theme.apply()


def _mtime(path) -> float:
    return path.stat().st_mtime if path.exists() else 0.0


@st.cache_data(ttl=3600, show_spinner="Calculando flows…")
def load_flows(version: float) -> pd.DataFrame:
    """`version` = history file mtime, so a new snapshot invalidates the cache immediately."""
    history = load_history()
    if history.empty:
        return pd.DataFrame()
    prices = fetch_prices(sorted(history["ticker"].unique()), start=history["as_of_date"].min() - pd.Timedelta(days=7))
    return compute_daily_flows(history, prices)


@st.cache_data(ttl=3600, show_spinner=False)
def load_monthly_flows(version: float) -> pd.DataFrame:
    monthly = load_monthly()
    if monthly.empty:
        return pd.DataFrame()
    prices = fetch_prices(sorted(monthly["ticker"].unique()), start=monthly["as_of_date"].min() - pd.Timedelta(days=7))
    return compute_monthly_flows(monthly, prices)


flows = load_flows(_mtime(HISTORY_FILE))
monthly = load_monthly_flows(_mtime(MONTHLY_FILE))
status = load_status()

with st.sidebar:
    st.markdown('<div class="desk-brand">ETF <span>Flows</span> Tracker</div>', unsafe_allow_html=True)
    st.caption("Creaciones y redenciones oficiales de 95 ETFs")

    session = None
    if not flows.empty:
        cov = session_coverage(flows)
        sessions = list(cov.index[::-1][:60])
        complete = latest_complete_date(flows)
        session = st.selectbox(
            "Sesión", sessions, index=sessions.index(complete) if complete in sessions else 0,
            format_func=lambda d: f"{pd.Timestamp(d):%a %d %b %Y} · {cov[d]} ETFs"
                                  + ("" if d <= complete else " · parcial"),
        )

    unit = st.segmented_control("Unidad", ["usd", "pct"], default="usd", format_func={"usd": "$", "pct": "% AUM"}.get)
    all_cats = get_categories()
    cats = st.pills("Categorías", all_cats, selection_mode="multi", default=all_cats)

    st.divider()
    n_total = len(get_tickers())
    if not status.empty:
        ok = int((status["status"] == "ok").sum())
        st.caption(f"**Cobertura diaria:** {ok}/{n_total} ETFs con fuente oficial")
        failing = status[status["status"].isin(["error", "rejected"])]
        if not failing.empty:
            st.warning(f"Fuentes con falla en la última corrida: {', '.join(failing['ticker'])}")
    if not flows.empty:
        st.caption(f"**Última sesión completa:** {latest_complete_date(flows):%d %b %Y}")
    st.caption("Datos reconstruidos con fuentes oficiales el 05-oct-2026.")
    if st.button("Refrescar datos", icon=":material/refresh:", width="stretch"):
        st.cache_data.clear()
        st.rerun()

ctx = Ctx(flows=flows, history=load_history(), status=status, monthly=monthly, session=session,
          categories=cats or all_cats, unit=unit or "usd")

pages = [
    st.Page(lambda: overview.render(ctx), title="Resumen", icon=":material/dashboard:", url_path="resumen", default=True),
    st.Page(lambda: rotation.render(ctx), title="Rotación", icon=":material/swap_horiz:", url_path="rotacion"),
    st.Page(lambda: signals.render(ctx), title="Señales", icon=":material/bolt:", url_path="senales"),
    st.Page(lambda: etf_detail.render(ctx), title="ETF", icon=":material/query_stats:", url_path="etf"),
    st.Page(lambda: vanguard_monthly.render(ctx), title="Vanguard mensual", icon=":material/calendar_month:",
            url_path="vanguard"),
    st.Page(lambda: volume.render(ctx), title="Volumen relativo", icon=":material/equalizer:", url_path="volumen"),
    st.Page(lambda: quality.render(ctx), title="Calidad", icon=":material/verified:", url_path="calidad"),
    st.Page(lambda: methodology.render(ctx), title="Metodología", icon=":material/menu_book:", url_path="metodologia"),
]
st.navigation(pages, position="top").run()
