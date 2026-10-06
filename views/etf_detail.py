"""Single-ETF drill-down: flow history, shares outstanding and NAV."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from config.universe import get_universe
from core.flows_calc import compute_zscore, window_flows
from ui import theme

from . import Ctx


def render(ctx: Ctx) -> None:
    f = ctx.flows
    if f.empty:
        theme.header("Detalle por ETF")
        st.info("Sin datos todavía.")
        return

    uni = get_universe()
    tickers = sorted(f["ticker"].unique())
    default = tickers.index("SPY") if "SPY" in tickers else 0
    head, pick = st.columns([3, 1], vertical_alignment="bottom")
    t = pick.selectbox("ETF", tickers, index=default, format_func=lambda x: f"{x} · {uni[x]['subcategory']}")
    meta = uni[t]
    d = f[f["ticker"] == t].sort_values("date")
    last = d.iloc[-1]

    with head:
        theme.header(f"{t} — {meta['name']}", f"{meta['category']} · {meta['issuer']}",
                     chips=[(f"fuente: {last['source']}", ""), (f"último dato {last['date']:%d %b %Y}", "")])

    v = d.dropna(subset=["flow_usd"])
    w = window_flows(v, ctx.session or d["date"].max(), (1, 5, 20, 60)).reindex([t]).iloc[0] if not v.empty else None
    z = compute_zscore(v)
    z_last = z.dropna(subset=["flow_z"])["flow_z"].iloc[-1] if z["flow_z"].notna().any() else float("nan")

    m = st.columns(6)
    m[0].metric("AUM", theme.usd(last["aum"], signed=False), border=True)
    m[1].metric("Shares", f"{last['shares_outstanding'] / 1e6:,.1f}M", border=True)
    for i, n in enumerate(("1D", "5D", "20D", "60D"), start=2):
        m[i].metric(f"Flow {n}", theme.usd(w[n]) if w is not None else "—", border=True)
    st.caption(f"Z-score último flow (60 sesiones, % AUM): {z_last:+.2f}" if pd.notna(z_last) else
               "Z-score disponible tras 10 sesiones con flow.")

    if v.empty:
        st.info("Este ETF aún no tiene dos publicaciones; el flow aparecerá con la siguiente.")
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=v["date"], y=v["flow_usd"] / 1e6, name="Flow diario ($M)",
                             marker_color=theme.sign_color(v["flow_usd"]),
                             hovertemplate="%{x|%d %b %Y}<br>%{y:+,.0f}M<extra></extra>"), secondary_y=False)
        fig.add_trace(go.Scatter(x=v["date"], y=v["flow_usd"].cumsum() / 1e9, name="Acumulado ($B)",
                                 line=dict(color=theme.ACCENT, width=2),
                                 hovertemplate="%{x|%d %b %Y}<br>%{y:+.2f}B<extra></extra>"), secondary_y=True)
        fig.update_layout(title="Flow diario y acumulado", bargap=0.15,
                          xaxis=dict(rangebreaks=theme.TRADING_RANGEBREAKS))
        fig.update_yaxes(title_text="$M", secondary_y=False)
        fig.update_yaxes(title_text="$B acumulado", secondary_y=True, showgrid=False)
        theme.chart(fig, height=380)

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Scatter(x=d["date"], y=d["shares_outstanding"] / 1e6, name="Shares (M)",
                              line=dict(color=theme.TEXT, width=2, shape="hv")), secondary_y=False)
    fig2.add_trace(go.Scatter(x=d["date"], y=d["price"], name="NAV",
                              line=dict(color=theme.MUTED, width=1.5, dash="dot")), secondary_y=True)
    fig2.update_layout(title="Shares outstanding (oficial) y NAV", xaxis=dict(rangebreaks=theme.TRADING_RANGEBREAKS))
    fig2.update_yaxes(title_text="Shares (M)", secondary_y=False)
    fig2.update_yaxes(title_text="NAV", secondary_y=True, showgrid=False)
    theme.chart(fig2, height=320)

    with st.expander("Datos por sesión"):
        st.dataframe(
            d.sort_values("date", ascending=False)[
                ["date", "shares_outstanding", "delta_shares", "price", "price_basis", "flow_usd",
                 "flow_pct_aum", "gap_days", "quality"]].rename(columns={
                "date": "Sesión", "shares_outstanding": "Shares", "delta_shares": "Δ Shares", "price": "NAV/precio",
                "price_basis": "Base", "flow_usd": "Flow ($)", "flow_pct_aum": "% AUM", "gap_days": "Sesiones",
                "quality": "Calidad"}),
            hide_index=True, width="stretch",
            column_config={"Sesión": st.column_config.DateColumn(format="YYYY-MM-DD"),
                           "Shares": st.column_config.NumberColumn(format="%,.0f"),
                           "Δ Shares": st.column_config.NumberColumn(format="%+,.0f"),
                           "Flow ($)": st.column_config.NumberColumn(format="%+,.0f"),
                           "% AUM": st.column_config.NumberColumn(format="percent")},
        )
