"""Rotation: where money is moving across categories over several horizons."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.flows_calc import category_flows, detect_rotation, sessions_up_to
from ui import theme

from . import Ctx

WINDOWS = (1, 5, 20, 60)


def _heatmap(ctx: Ctx) -> None:
    frames = []
    for n in WINDOWS:
        cf = category_flows(ctx.valid, ctx.session, n)
        frames.append(cf.assign(window=f"{n}D"))
    grid = pd.concat(frames, ignore_index=True)
    if grid.empty:
        st.info("Sin datos suficientes.")
        return
    col = "flow_pct" if ctx.unit == "pct" else "flow_usd"
    piv = grid.pivot(index="category", columns="window", values=col)[[f"{n}D" for n in WINDOWS]]
    piv = piv.loc[piv["20D"].fillna(0).sort_values().index]
    z = piv.to_numpy(dtype=float)
    # colour each column on its own scale: a 60D sum dwarfs a 1D sum
    scale = np.nanmax(np.abs(np.nan_to_num(z)), axis=0, keepdims=True)
    zn = z / np.where(scale == 0, 1, scale)
    text = [[(theme.pct(v) if ctx.unit == "pct" else theme.usd(v)) if not np.isnan(v) else "—" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=zn, x=list(piv.columns), y=list(piv.index), text=text, texttemplate="%{text}",
        textfont=dict(color="#F8FAFC", size=12),
        colorscale=theme.DIVERGING, zmid=0, zmin=-1, zmax=1, showscale=False, xgap=3, ygap=3,
        hovertemplate="%{y} · %{x}<br>%{text}<extra></extra>",
    ))
    fig.update_layout(title=dict(text="Flow neto acumulado por ventana (color relativo dentro de cada ventana)",
                                 y=0.99, yanchor="top"),
                      xaxis=dict(side="top", showgrid=False), yaxis=dict(showgrid=False),
                      margin=dict(l=8, r=8, t=64, b=8))
    theme.chart(fig, height=max(380, 36 * len(piv) + 100))


def _cumulative(ctx: Ctx, n: int) -> None:
    v = ctx.valid
    dates = sessions_up_to(v, ctx.session, n)
    d = v[v["date"].isin(dates)].groupby(["date", "category"])["flow_usd"].sum().unstack().fillna(0).cumsum() / 1e9
    if d.empty:
        return
    order = d.iloc[-1].sort_values(ascending=False).index
    fig = go.Figure()
    for c in order:
        fig.add_trace(go.Scatter(x=d.index, y=d[c], name=c, mode="lines", line=dict(width=2),
                                 hovertemplate=f"{c}<br>%{{x|%d %b}}: %{{y:+.2f}}B<extra></extra>"))
    fig.update_layout(title=f"Flow acumulado por categoría · últimas {len(dates)} sesiones ($B)",
                      legend=dict(orientation="v", y=1, x=1.02), margin=dict(l=8, r=8, t=36, b=8),
                      xaxis=dict(rangebreaks=theme.TRADING_RANGEBREAKS))
    theme.chart(fig, height=420)


def _rotation_signal(ctx: Ctx) -> None:
    rot = detect_rotation(ctx.valid[ctx.valid["date"] <= ctx.session], short=5, long=20)
    if rot.empty:
        return
    rot = rot.sort_values("rotation_b")
    fig = go.Figure(go.Bar(
        x=rot["rotation_b"], y=rot["category"], orientation="h", marker_color=theme.sign_color(rot["rotation_b"]),
        customdata=np.c_[rot["flow_short_b"], rot["flow_long_b"]],
        hovertemplate="%{y}<br>Señal %{x:+.2f}B<br>Últimas 5: %{customdata[0]:+.2f}B"
                      "<br>15 previas: %{customdata[1]:+.2f}B<extra></extra>",
    ))
    fig.update_layout(title="Aceleración: últimas 5 sesiones vs. ritmo de las 15 previas ($B)",
                      yaxis=dict(showgrid=False))
    theme.chart(fig, height=max(300, 30 * len(rot) + 60))


def render(ctx: Ctx) -> None:
    theme.header("Rotación", "Hacia dónde se mueve el dinero entre clases de activo y en qué horizonte")
    if ctx.session is None or ctx.valid.empty:
        st.info("Sin flows válidos todavía.")
        return
    st.caption("Ventanas en sesiones de trading que terminan en la sesión seleccionada. iShares e Invesco tienen "
               "historial sólo desde oct-2026, así que sus ventanas largas aún están incompletas.")
    _heatmap(ctx)
    a, b = st.columns([3, 2], gap="large")
    with a:
        n = st.segmented_control("Horizonte", [20, 60, 120], default=60, format_func=lambda x: f"{x} sesiones")
        _cumulative(ctx, n or 60)
    with b:
        _rotation_signal(ctx)
