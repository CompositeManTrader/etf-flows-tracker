"""Intraday tab: relative-volume proxy (NOT official flow)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.universe import get_universe
from data.price_loader import fetch_intraday_quote


@st.cache_data(ttl=300)
def _cached_intraday() -> pd.DataFrame:
    return fetch_intraday_quote()


def render() -> None:
    st.subheader("Intraday Pressure")
    st.caption(
        "⚠️ NO es flow oficial. Es un proxy de presión basado en **volumen relativo** "
        "(volumen de hoy / ADV20). Útil intraday cuando los snapshots de shares aún no llegan."
    )

    if st.button("Actualizar snapshot intraday"):
        _cached_intraday.clear()

    df = _cached_intraday()

    if df is None or df.empty:
        st.warning("No se pudieron obtener quotes. Reintenta en unos segundos.")
        return

    universe = get_universe()
    df = df.copy()
    df["category"] = df["ticker"].map(lambda t: universe.get(t, {}).get("category"))
    df["name"] = df["ticker"].map(lambda t: universe.get(t, {}).get("name"))

    cats = sorted(df["category"].dropna().unique().tolist())
    selected = st.multiselect("Categorías", cats, default=cats)
    if selected:
        df = df[df["category"].isin(selected)]

    df = df.dropna(subset=["rel_volume"]).sort_values("rel_volume", ascending=False)
    if df.empty:
        st.info("Sin datos de volumen relativo disponibles.")
        return

    top = df.head(20).sort_values("rel_volume")
    fig = px.bar(
        top, x="rel_volume", y="ticker", orientation="h",
        color="rel_volume", color_continuous_scale="Reds",
        labels={"rel_volume": "Vol Hoy / ADV20", "ticker": ""},
        title="Top 20 — Volumen Relativo",
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Tabla completa"):
        out = df[["ticker", "name", "category", "last_price", "last_session_volume", "adv20", "rel_volume", "as_of"]].copy()
        out["rel_volume"] = out["rel_volume"].round(2)
        st.dataframe(out, hide_index=True, use_container_width=True)
