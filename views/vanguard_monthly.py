"""Vanguard monthly flows (Vanguard publishes ETF shares outstanding only at month end)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.universe import get_universe
from data.sources.vanguard import TICKERS
from ui import theme

from . import Ctx


def render(ctx: Ctx) -> None:
    theme.header("Vanguard · mensual",
                 "VOO, VTI y el resto de ETFs de Vanguard: flow de cierre de mes a cierre de mes",
                 chips=[("granularidad mensual", "warn")])
    st.caption("Vanguard sólo publica las shares de sus ETFs al cierre de cada mes, así que estos flows no se "
               "mezclan con la vista diaria. Flow = (Shares fin de mes − Shares mes previo) × NAV de fin de mes.")

    m = ctx.monthly
    uni = get_universe()
    if m.empty:
        st.info("Aún no hay cierres de mes guardados. El job los toma en cada corrida.")
        return

    months = sorted(m["date"].unique())
    latest = m[m["date"] == months[-1]].set_index("ticker")
    table = pd.DataFrame({"ETF": list(TICKERS)}).merge(
        latest.reset_index().rename(columns={"ticker": "ETF"}), on="ETF", how="left")
    table = pd.DataFrame({
        "ETF": table["ETF"],
        "Nombre": [uni[t]["subcategory"] for t in table["ETF"]],
        "Cierre de mes": table["date"],
        "Shares (M)": table["shares_outstanding"] / 1e6,
        "NAV": table["price"],
        "AUM ($B)": table["aum"] / 1e9,
        "Flow del mes ($M)": pd.to_numeric(table["flow_usd"], errors="coerce") / 1e6,
        "% AUM": pd.to_numeric(table["flow_pct_aum"], errors="coerce") * 100,
    })

    flows_ready = table["Flow del mes ($M)"].notna().any()
    k = st.columns(3)
    k[0].metric("Último cierre de mes", f"{pd.Timestamp(months[-1]):%d %b %Y}", border=True)
    k[1].metric("Flow neto del mes", theme.usd(table["Flow del mes ($M)"].sum() * 1e6) if flows_ready else "—",
                border=True)
    k[2].metric("AUM ETFs Vanguard", theme.usd(table["AUM ($B)"].sum() * 1e9, signed=False), border=True)

    if not flows_ready:
        next_me = (pd.Timestamp(months[-1]) + pd.offsets.MonthEnd(1)).date()
        st.info(f"Primer cierre registrado: {pd.Timestamp(months[0]):%d %b %Y}. El primer flow mensual aparece cuando "
                f"Vanguard publique el cierre del {next_me:%d %b %Y} (unos días después de esa fecha).")
    else:
        d = table.dropna(subset=["Flow del mes ($M)"]).sort_values("Flow del mes ($M)")
        fig = go.Figure(go.Bar(x=d["Flow del mes ($M)"], y=d["ETF"], orientation="h",
                               marker_color=theme.sign_color(d["Flow del mes ($M)"]),
                               text=[theme.usd(v * 1e6) for v in d["Flow del mes ($M)"]], textposition="outside",
                               cliponaxis=False))
        fig.update_layout(title=f"Flow del mes · {pd.Timestamp(months[-1]):%B %Y}",
                          xaxis=dict(showticklabels=False, showgrid=False), margin=dict(l=8, r=60, t=36, b=8))
        theme.chart(fig, height=360)

    if not flows_ready:  # Streamlit renders empty cells as "None"; hide the flow columns until they exist
        table = table.drop(columns=["Flow del mes ($M)", "% AUM"])
    st.dataframe(table, hide_index=True, width="stretch", column_config={
        "Cierre de mes": st.column_config.DateColumn(format="YYYY-MM-DD"),
        "Shares (M)": st.column_config.NumberColumn(format="%,.1f"),
        "NAV": st.column_config.NumberColumn(format="%.2f"),
        "AUM ($B)": st.column_config.NumberColumn(format="%,.1f"),
        "Flow del mes ($M)": st.column_config.NumberColumn(format="%+,.0f"),
        "% AUM": st.column_config.NumberColumn(format="%+.2f%%"),
    })

    if len(months) > 1:
        with st.expander("Historial mensual"):
            hist = m.pivot_table(index="date", columns="ticker", values="flow_usd") / 1e6
            st.dataframe(hist.sort_index(ascending=False), width="stretch")
