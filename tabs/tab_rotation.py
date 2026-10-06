"""Rotation map: heatmap categoría × ventana + rotation signal 5D vs 20D."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.flows_calc import aggregate_by_category, detect_rotation, latest_complete_date


def render(flows: pd.DataFrame) -> None:
    st.subheader("Rotation Map")

    if flows is None or flows.empty:
        st.warning("No hay flows. Necesitas histórico para ver rotación.")
        return

    f = flows.dropna(subset=["flow_usd", "date"]).copy()
    if f.empty:
        st.warning("Sin datos de flows válidos.")
        return

    windows = {"1D": 1, "5D": 5, "20D": 20, "60D": 60}
    st.caption(f"Ventanas en sesiones de trading hasta la última sesión completa ({latest_complete_date(f).date()}).")

    rows = []
    for label, days in windows.items():
        for _, r in aggregate_by_category(f, period_days=days).iterrows():
            rows.append({"category": r["category"], "window": label, "flow_b": float(r["flow_usd_b"])})

    grid = pd.DataFrame(rows)
    if grid.empty:
        st.info("Sin datos para construir el heatmap.")
        return

    pivot = grid.pivot(index="category", columns="window", values="flow_b").fillna(0.0)
    pivot = pivot[[w for w in windows if w in pivot.columns]]

    fig = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        text_auto=".2f",
        aspect="auto",
        labels={"color": "Flow ($B)"},
        title="Heatmap: Flows acumulados por categoría × ventana",
    )
    fig.update_layout(height=max(400, 32 * len(pivot)))
    st.plotly_chart(fig, width="stretch")

    st.markdown("### Rotation Signal (5D vs 20D)")
    rot = detect_rotation(f, short=5, long=20)
    if rot.empty:
        st.info("Sin señal de rotación calculable.")
        return

    fig2 = px.bar(
        rot.sort_values("rotation_b"),
        x="rotation_b", y="category",
        orientation="h",
        color="rotation_b",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        labels={"rotation_b": "Rotation ($B)", "category": ""},
    )
    fig2.update_layout(height=max(300, 28 * len(rot)))
    st.plotly_chart(fig2, width="stretch")

    with st.expander("Tabla detalle rotación"):
        st.dataframe(rot.round(2), hide_index=True, width="stretch")
