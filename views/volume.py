"""Relative volume: last session's volume vs. its 20-day average (a pressure proxy, NOT a flow)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.universe import get_universe
from data.price_loader import fetch_intraday_quote
from ui import theme

from . import Ctx

HOT = 2.0


@st.cache_data(ttl=300)
def _quotes() -> pd.DataFrame:
    return fetch_intraday_quote()


def render(ctx: Ctx) -> None:
    theme.header("Volumen relativo", "Volumen de la última sesión ÷ promedio de 20 días · cubre los 95 ETFs",
                 chips=[("proxy de presión, no es flow", "warn")])
    st.caption("Útil para ver presión en ETFs sin shares diarias (VOO, VTI, ARKK…) y para anticipar creaciones "
               "o redenciones antes de que el issuer publique. Un volumen alto no indica dirección.")

    df = _quotes()
    if df is None or df.empty:
        st.warning("No se pudieron obtener precios. Reintenta en unos segundos.")
        return
    uni = get_universe()
    df = df.assign(category=df["ticker"].map(lambda t: uni.get(t, {}).get("category")),
                   name=df["ticker"].map(lambda t: uni.get(t, {}).get("name")))
    if ctx.categories:
        df = df[df["category"].isin(ctx.categories)]
    df = df.dropna(subset=["rel_volume"]).sort_values("rel_volume", ascending=False)
    if df.empty:
        st.info("Sin datos de volumen relativo.")
        return

    k = st.columns(3)
    k[0].metric(f"ETFs con volumen ≥ {HOT:.0f}× ADV20", int((df["rel_volume"] >= HOT).sum()), border=True)
    k[1].metric("Mediana vol. relativo", f"{df['rel_volume'].median():.2f}×", border=True)
    k[2].metric("Datos al", f"{pd.Timestamp(df['as_of'].iloc[0]):%d %b %H:%M} UTC", border=True)

    top = df.head(25).sort_values("rel_volume")
    fig = go.Figure(go.Bar(
        x=top["rel_volume"], y=top["ticker"], orientation="h",
        marker_color=["#F5A524" if v >= HOT else theme.NEUTRAL for v in top["rel_volume"]],
        customdata=top[["name", "last_session_volume", "adv20"]].to_numpy(),
        hovertemplate="%{y} · %{customdata[0]}<br>%{x:.2f}× ADV20<br>Vol %{customdata[1]:,.0f} · "
                      "ADV20 %{customdata[2]:,.0f}<extra></extra>",
    ))
    fig.add_vline(x=1, line=dict(color=theme.MUTED, dash="dot", width=1))
    fig.update_layout(title="Top 25 por volumen relativo", yaxis=dict(showgrid=False))
    theme.chart(fig, height=640)

    with st.expander("Tabla completa"):
        st.dataframe(
            df[["ticker", "name", "category", "last_price", "last_session_volume", "adv20", "rel_volume"]].rename(
                columns={"ticker": "ETF", "name": "Nombre", "category": "Categoría", "last_price": "Precio",
                         "last_session_volume": "Volumen", "adv20": "ADV20", "rel_volume": "Vol. relativo"}),
            hide_index=True, width="stretch",
            column_config={"Volumen": st.column_config.NumberColumn(format="%,.0f"),
                           "ADV20": st.column_config.NumberColumn(format="%,.0f"),
                           "Vol. relativo": st.column_config.NumberColumn(format="%.2f×")},
        )
