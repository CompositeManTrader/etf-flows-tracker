"""Signals tab: z-score anomaly detection."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.flows_calc import compute_zscore


def render(flows: pd.DataFrame) -> None:
    st.subheader("Signals — Anomalías Z-score")

    if flows is None or flows.empty:
        st.warning("No hay flows. Necesitas histórico para detectar anomalías.")
        return

    c1, c2 = st.columns(2)
    window = c1.slider("Ventana z-score (días)", 20, 120, 60, step=5)
    threshold = c2.slider("Umbral |z|", 1.0, 3.0, 2.0, step=0.1)

    z = compute_zscore(flows, window=window)
    if z.empty:
        st.warning("Sin datos.")
        return

    last_date = z["date"].max()
    last = z[z["date"] == last_date].dropna(subset=["flow_z"])
    anomalies = last[last["flow_z"].abs() >= threshold].copy()

    if anomalies.empty:
        st.info(f"Sin anomalías al {pd.Timestamp(last_date).date()} con umbral |z| ≥ {threshold}.")
        return

    anomalies = anomalies.sort_values("flow_z")
    fig = px.bar(
        anomalies,
        x="flow_z", y="ticker",
        orientation="h",
        color="flow_z",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
        labels={"flow_z": "Z-score", "ticker": ""},
        title=f"Anomalías ({pd.Timestamp(last_date).date()}) — |z| ≥ {threshold}",
    )
    fig.update_layout(height=max(400, 25 * len(anomalies)))
    st.plotly_chart(fig, use_container_width=True)

    tbl = anomalies[["ticker", "name", "category", "flow_usd", "flow_z"]].copy()
    tbl["Flow ($M)"] = (tbl["flow_usd"] / 1e6).round(1)
    tbl["Z-score"] = tbl["flow_z"].round(2)
    st.dataframe(
        tbl[["ticker", "name", "category", "Flow ($M)", "Z-score"]],
        hide_index=True, use_container_width=True,
    )
