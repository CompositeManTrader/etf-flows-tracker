"""Signals: flows that are unusual for that ETF's own history."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from core.flows_calc import compute_zscore
from ui import theme

from . import Ctx


def render(ctx: Ctx) -> None:
    theme.header("Señales", "Flows fuera de lo normal para cada ETF, medidos contra su propio historial")
    if ctx.session is None or ctx.valid.empty:
        st.info("Sin flows válidos todavía.")
        return

    c1, c2, _ = st.columns([1, 1, 2])
    window = c1.slider("Ventana (sesiones)", 20, 120, 60, step=5)
    threshold = c2.slider("Umbral |z|", 1.0, 4.0, 2.0, step=0.1)

    z = compute_zscore(ctx.valid, window=window)
    day = z[(z["date"] == ctx.session)].dropna(subset=["flow_z"])
    if day.empty:
        st.info("Ningún ETF tiene historial suficiente (≥10 sesiones) en esta sesión.")
        return
    hot = day[day["flow_z"].abs() >= threshold]

    m = st.columns(3)
    m[0].metric("ETFs evaluados", len(day), border=True)
    m[1].metric("Anomalías", len(hot), border=True)
    m[2].metric("Flow en anomalías", theme.usd(hot["flow_usd"].sum()), border=True)

    calm = day[day["flow_z"].abs() < threshold]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=calm["flow_pct_aum"] * 100, y=calm["flow_z"], mode="markers", name="Normal",
        marker=dict(size=8, color=theme.NEUTRAL, opacity=0.55), text=calm["ticker"],
        hovertemplate="%{text}<br>%{x:+.2f}% AUM · z %{y:+.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=hot["flow_pct_aum"] * 100, y=hot["flow_z"], mode="markers+text", name="Anomalía",
        marker=dict(size=13, color=theme.sign_color(hot["flow_z"]), line=dict(width=1, color=theme.TEXT)),
        text=hot["ticker"], textposition="top center", textfont=dict(size=11),
        hovertemplate="%{text}<br>%{x:+.2f}% AUM · z %{y:+.1f}<extra></extra>",
    ))
    for y in (threshold, -threshold):
        fig.add_hline(y=y, line=dict(color=theme.MUTED, width=1, dash="dot"))
    fig.update_layout(title=f"Flow de la sesión vs. su z-score ({window} sesiones)",
                      xaxis_title="Flow % AUM", yaxis_title="z-score")
    theme.chart(fig, height=460)

    if not hot.empty:
        t = hot.sort_values("flow_z", key=abs, ascending=False)
        st.dataframe(
            t.assign(**{"Flow ($M)": t["flow_usd"] / 1e6, "% AUM": t["flow_pct_aum"] * 100})
             .rename(columns={"ticker": "ETF", "name": "Nombre", "category": "Categoría", "flow_z": "z"})
             [["ETF", "Nombre", "Categoría", "Flow ($M)", "% AUM", "z"]],
            hide_index=True, width="stretch",
            column_config={"Flow ($M)": st.column_config.NumberColumn(format="%+.0f"),
                           "% AUM": st.column_config.NumberColumn(format="%+.2f%%"),
                           "z": st.column_config.NumberColumn(format="%+.2f")},
        )
