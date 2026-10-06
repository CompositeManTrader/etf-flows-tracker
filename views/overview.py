"""Overview: what moved in the selected session, at a glance."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config.universe import WATCHLIST, get_universe
from core.flows_calc import category_flows, compute_zscore, risk_appetite, sessions_up_to, window_flows
from ui import theme

from . import Ctx


def _kpis(ctx: Ctx, day: pd.DataFrame) -> None:
    net = day["flow_usd"].sum()
    inflow = day.loc[day["flow_usd"] > 0, "flow_usd"].sum()
    outflow = day.loc[day["flow_usd"] < 0, "flow_usd"].sum()
    n_in, n_out = int((day["flow_usd"] > 0).sum()), int((day["flow_usd"] < 0).sum())
    score, on, off = risk_appetite(day)
    label = "Risk-on" if score > 0.2 else "Risk-off" if score < -0.2 else "Neutral"

    c = st.columns(5)
    c[0].metric("Flow neto", theme.usd(net), border=True)
    c[1].metric("Entradas", theme.usd(inflow), border=True)
    c[2].metric("Salidas", theme.usd(outflow), border=True)
    c[3].metric("Amplitud", f"{n_in} ↑ · {n_out} ↓", border=True,
                help="ETFs con creaciones netas vs. con redenciones netas en la sesión.")
    c[4].metric("Sesgo de riesgo", f"{label} {score:+.2f}", border=True,
                help=(f"(risk-on − risk-off) / (|risk-on| + |risk-off|). Risk-on {theme.usd(on)}: renta variable, "
                      f"high yield, cripto, short vol. Risk-off {theme.usd(off)}: Treasuries, T-bills, oro, long vol, "
                      "min-vol. Neutral (IG, MBS, commodities ex-oro) no cuenta."))


def _category_chart(ctx: Ctx) -> None:
    cf = category_flows(ctx.valid, ctx.session, 1)
    if cf.empty:
        st.info("Sin flows por categoría para esta sesión.")
        return
    col = "flow_pct" if ctx.unit == "pct" else "flow_usd"
    cf = cf.sort_values(col)
    text = [theme.pct(v) if ctx.unit == "pct" else theme.usd(v) for v in cf[col]]
    fig = go.Figure(go.Bar(
        x=cf[col], y=cf["category"], orientation="h", marker_color=theme.sign_color(cf[col]),
        text=text, textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{text}<extra></extra>",
    ))
    fig.update_layout(title="Flow neto por categoría",
                      xaxis=dict(showticklabels=False, showgrid=False, range=theme.padded_range(cf[col])),
                      yaxis=dict(showgrid=False), bargap=0.35)
    theme.chart(fig, height=max(320, 30 * len(cf) + 60))


def _watchlist(ctx: Ctx) -> None:
    v = ctx.flows.dropna(subset=["flow_usd"])
    have = [t for t in WATCHLIST if t in set(v["ticker"])]
    if not have:
        st.info("Ningún ETF de la watchlist tiene flows aún.")
        return
    w = window_flows(v, ctx.session, (1, 5, 20)).reindex(have)
    z = compute_zscore(v)
    zs = z[z["date"] == ctx.session].set_index("ticker")["flow_z"]
    dates = sessions_up_to(v, ctx.session, 20)
    spark = (v[v["date"].isin(dates) & v["ticker"].isin(have)]
             .pivot_table(index="ticker", columns="date", values="flow_usd").reindex(have))

    uni = get_universe()
    table = pd.DataFrame({
        "ETF": have,
        "Nombre": [uni[t]["subcategory"] for t in have],
        "Sesión": [w.loc[t, "1D"] / 1e6 for t in have],
        "5D": [w.loc[t, "5D"] / 1e6 for t in have],
        "20D": [w.loc[t, "20D"] / 1e6 for t in have],
        "z": [zs.get(t) for t in have],
        "Últimas 20": [[0 if pd.isna(x) else x / 1e6 for x in spark.loc[t].tolist()] for t in have],
    })
    st.dataframe(
        table, hide_index=True, width="stretch", height=36 * len(table) + 40,
        column_config={
            "Sesión": st.column_config.NumberColumn(format="%+.0f M"),
            "5D": st.column_config.NumberColumn(format="%+.0f M"),
            "20D": st.column_config.NumberColumn(format="%+.0f M"),
            "z": st.column_config.NumberColumn(format="%+.1f", help="Z-score del flow (% AUM) vs. 60 sesiones"),
            "Últimas 20": st.column_config.BarChartColumn(help="Flow diario, últimas 20 sesiones ($M)"),
        },
    )


def _movers(ctx: Ctx, day: pd.DataFrame) -> None:
    col = ctx.value_col
    cols = {"ticker": "ETF", "name": "Nombre", "category": "Categoría"}
    left, right = st.columns(2)
    for side, target, title in ((False, left, "Mayores entradas"), (True, right, "Mayores salidas")):
        d = day.sort_values(col, ascending=side).head(10)
        d = d[d[col] < 0] if side else d[d[col] > 0]
        with target:
            theme.section(title)
            t = d.rename(columns=cols).assign(**{
                "Flow ($M)": d["flow_usd"] / 1e6, "% AUM": d["flow_pct_aum"] * 100,
            })[["ETF", "Nombre", "Flow ($M)", "% AUM"]]
            st.dataframe(t, hide_index=True, width="stretch", column_config={
                "ETF": st.column_config.TextColumn(width="small"),
                "Nombre": st.column_config.TextColumn(width="medium"),
                "Flow ($M)": st.column_config.NumberColumn(format="%+.0f", width="small"),
                "% AUM": st.column_config.NumberColumn(format="%+.2f%%", width="small"),
            })


def _treemap(day: pd.DataFrame) -> None:
    d = day.assign(size=day["flow_usd"].abs(), pct=day["flow_pct_aum"] * 100,
                   label=[f"{t}<br>{theme.usd(f)}" for t, f in zip(day["ticker"], day["flow_usd"])])
    d = d[d["size"] > 0]
    if d.empty:
        return
    lim = max(0.5, d["pct"].abs().quantile(0.9))
    fig = px.treemap(d, path=[px.Constant("Universo"), "category", "ticker"], values="size",
                     color="pct", color_continuous_scale=theme.DIVERGING, range_color=(-lim, lim),
                     custom_data=["flow_usd", "pct", "name"])
    fig.update_traces(
        marker=dict(line=dict(width=1, color=theme.BORDER)), root_color=theme.SURFACE,
        hovertemplate="<b>%{label}</b> %{customdata[2]}<br>Flow $%{customdata[0]:,.0f}<br>%{customdata[1]:+.2f}% AUM<extra></extra>",
        texttemplate="%{label}", textfont=dict(size=12),
    )
    fig.update_layout(title="Mapa de flows · tamaño = |flow $|, color = flow % AUM",
                      coloraxis_colorbar=dict(title="% AUM", ticksuffix="%"), margin=dict(l=4, r=4, t=36, b=4))
    theme.chart(fig, height=520)


def render(ctx: Ctx) -> None:
    if ctx.session is None:
        theme.header("Resumen")
        st.info("Aún no hay flows válidos. Se necesitan al menos dos publicaciones por ETF.")
        return
    day = ctx.day()
    theme.header(
        "Resumen de flows",
        f"Creaciones/redenciones oficiales · sesión {ctx.session:%d %b %Y}",
        chips=[(f"{day['ticker'].nunique()} ETFs con dato", "")],
    )
    if day.empty:
        st.info("Sin flows para las categorías seleccionadas en esta sesión.")
        return

    _kpis(ctx, day)
    st.write("")
    a, b = st.columns([5, 6], gap="large")
    with a:
        _category_chart(ctx)
    with b:
        theme.section("Termómetro de la mesa")
        _watchlist(ctx)
    _movers(ctx, day)
    _treemap(day)
