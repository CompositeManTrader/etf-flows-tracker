"""Signals tab: z-score anomalies on flow as % of AUM."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.flows_calc import compute_zscore, latest_complete_date


def render(flows: pd.DataFrame) -> None:
    st.subheader("Signals — Anomalías Z-score")
    st.caption(
        "Z-score del flow como % del AUM contra el propio histórico de cada ETF. "
        "Normalizar por AUM evita que los ETFs gigantes dominen sólo por tamaño."
    )

    if flows is None or flows.empty:
        st.warning("No hay flows. Necesitas histórico para detectar anomalías.")
        return

    c1, c2 = st.columns(2)
    window = c1.slider("Ventana z-score (sesiones)", 20, 120, 60, step=5)
    threshold = c2.slider("Umbral |z|", 1.0, 4.0, 2.0, step=0.1)

    z = compute_zscore(flows, window=window)
    last_date = latest_complete_date(flows)
    if z.empty or last_date is None:
        st.warning("Sin datos.")
        return

    last = z[z["date"] == last_date].dropna(subset=["flow_z"])
    anomalies = last[last["flow_z"].abs() >= threshold].copy()
    n_scored = len(last)

    if anomalies.empty:
        st.info(f"Sin anomalías al {last_date.date()} con |z| ≥ {threshold} ({n_scored} ETFs con historial suficiente).")
        return

    anomalies = anomalies.sort_values("flow_z")
    fig = px.bar(
        anomalies, x="flow_z", y="ticker", orientation="h",
        color="flow_z", color_continuous_scale="RdBu", color_continuous_midpoint=0,
        labels={"flow_z": "Z-score", "ticker": ""},
        title=f"Anomalías ({last_date.date()}) — |z| ≥ {threshold} · {n_scored} ETFs evaluados",
    )
    fig.update_layout(height=max(400, 25 * len(anomalies)))
    st.plotly_chart(fig, width="stretch")

    tbl = anomalies.assign(**{
        "Flow ($M)": (anomalies["flow_usd"] / 1e6).round(1),
        "% AUM": (anomalies["flow_pct_aum"] * 100).round(2),
        "Z-score": anomalies["flow_z"].round(2),
    })
    st.dataframe(tbl[["ticker", "name", "category", "Flow ($M)", "% AUM", "Z-score"]],
                 hide_index=True, width="stretch")
