"""Sectors: where institutional money is going in and out, sector by sector, every session."""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.universe import SECTOR_ES, sector_of
from core.flows_calc import sessions_up_to
from core.sectors import (
    daily_reading, industry_panel, sector_daily, sector_panel, sector_session, with_sector,
)
from ui import theme

from . import Ctx


def _streak_label(n) -> str:
    if not n:
        return "—"
    return f"▲ {n}" if n > 0 else f"▼ {abs(n)}"


def _bar(panel: pd.DataFrame, unit: str) -> None:
    col = "pct_1D" if unit == "pct" else "flow_1D"
    d = panel[panel["has_session"]].dropna(subset=[col]).sort_values(col)
    if d.empty:
        st.info("Sin flows sectoriales en esta sesión.")
        return
    text = [theme.pct(v) if unit == "pct" else theme.usd(v) for v in d[col]]
    fig = go.Figure(go.Bar(
        x=d[col], y=d["sector_es"], orientation="h", marker_color=theme.sign_color(d[col]),
        text=text, textposition="outside", cliponaxis=False,
        customdata=np.c_[d["flow_5D"] / 1e6, d["flow_20D"] / 1e6],
        hovertemplate="%{y}<br>Sesión %{text}<br>5D %{customdata[0]:+,.0f}M · 20D %{customdata[1]:+,.0f}M<extra></extra>",
    ))
    fig.update_layout(title="Flow neto por sector en la sesión",
                      xaxis=dict(showticklabels=False, showgrid=False, range=theme.padded_range(d[col])),
                      yaxis=dict(showgrid=False), bargap=0.3)
    theme.chart(fig, height=420)


def _scoreboard(panel: pd.DataFrame) -> None:
    p = panel.sort_values("flow_1D", ascending=False, na_position="last")
    table = pd.DataFrame({
        "Sector": p["sector_es"],
        "Sesión": p["flow_1D"] / 1e6,
        "5D": p["flow_5D"] / 1e6,
        "20D": p["flow_20D"] / 1e6,
        "60D": p["flow_60D"] / 1e6,
        "20D % AUM": p["pct_20D"] * 100,
        "z": p["z"],
        "Racha": [_streak_label(s) for s in p["streak"]],
        "Últimas 20": p["spark"],
    })
    st.dataframe(table, hide_index=True, width="stretch", height=36 * len(table) + 40, column_config={
        "Sector": st.column_config.TextColumn(width="medium"),
        "Sesión": st.column_config.NumberColumn(format="%+.0f M", help="Flow neto de la sesión ($M)"),
        "5D": st.column_config.NumberColumn(format="%+.0f M"),
        "20D": st.column_config.NumberColumn(format="%+.0f M"),
        "60D": st.column_config.NumberColumn(format="%+.0f M"),
        "20D % AUM": st.column_config.NumberColumn(format="%+.2f%%", help="Flow 20 sesiones ÷ AUM del sector al inicio"),
        "z": st.column_config.NumberColumn(format="%+.1f", help="Flow de la sesión (% AUM) vs. sus 60 sesiones previas"),
        "Racha": st.column_config.TextColumn(help="Sesiones consecutivas con entradas (▲) o salidas (▼)"),
        "Últimas 20": st.column_config.BarChartColumn(help="Flow diario del sector, últimas 20 sesiones ($M)"),
    })


def _heatmap(sf: pd.DataFrame, session, unit: str, n: int = 20) -> None:
    daily = sector_daily(sf)
    dates = sessions_up_to(daily, session, n)
    d = daily[daily["date"].isin(dates)]
    col = "flow_pct" if unit == "pct" else "flow_usd"
    piv = d.pivot(index="sector", columns="date", values=col)
    if piv.empty:
        return
    order = piv.sum(axis=1).sort_values().index
    piv = piv.loc[order]
    z = piv.to_numpy(dtype=float)
    lim = np.nanquantile(np.abs(z), 0.95) if np.isfinite(z).any() else 1
    fmt = (lambda v: theme.pct(v)) if unit == "pct" else (lambda v: theme.usd(v))
    hover = [[fmt(v) if not np.isnan(v) else "sin dato" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=[pd.Timestamp(c).strftime("%d %b") for c in piv.columns], y=[SECTOR_ES[s] for s in piv.index],
        customdata=hover, colorscale=theme.DIVERGING, zmid=0, zmin=-lim, zmax=lim, showscale=False,
        xgap=2, ygap=2, hovertemplate="%{y} · %{x}<br>%{customdata}<extra></extra>",
    ))
    fig.update_layout(title=f"Persistencia: flow diario por sector, últimas {len(dates)} sesiones",
                      xaxis=dict(showgrid=False, type="category", tickangle=-50, tickfont=dict(size=10)),
                      yaxis=dict(showgrid=False))
    theme.chart(fig, height=440)


def _quadrant(panel: pd.DataFrame, n: int) -> None:
    d = panel.dropna(subset=[f"pct_{n}D", f"ret_{n}D"])
    if d.empty:
        st.info("Sin datos suficientes para esta ventana.")
        return
    x, y = d[f"ret_{n}D"] * 100, d[f"pct_{n}D"] * 100
    size = 14 + 36 * np.sqrt(d["aum"] / d["aum"].max())
    # alternate label above/below by rank on the y axis so neighbouring bubbles don't overprint
    rank = y.rank(method="first").astype(int)
    positions = ["top center" if r % 2 else "bottom center" for r in rank]
    fig = go.Figure(go.Scatter(
        x=x, y=y, mode="markers+text", text=d["sector_es"], textposition=positions,
        textfont=dict(size=11, color=theme.TEXT),
        marker=dict(size=size, color=theme.sign_color(y), opacity=0.8, line=dict(width=1, color=theme.BORDER)),
        customdata=np.c_[d[f"flow_{n}D"] / 1e6],
        hovertemplate="%{text}<br>Rendimiento %{x:+.2f}%<br>Flow %{y:+.2f}% AUM (%{customdata[0]:+,.0f}M)<extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color=theme.MUTED, width=1))
    fig.add_vline(x=0, line=dict(color=theme.MUTED, width=1))
    xr = max(abs(x.min()), abs(x.max())) * 1.25 or 1
    yr = max(abs(y.min()), abs(y.max())) * 1.25 or 1
    for tx, ty, label in ((xr, yr, "Compran fuerza"), (-xr, yr, "Compran la caída"),
                          (xr, -yr, "Venden el rebote"), (-xr, -yr, "Capitulación")):
        fig.add_annotation(x=tx * 0.95, y=ty * 0.95, text=label, showarrow=False,
                           xanchor="right" if tx > 0 else "left", yanchor="top" if ty > 0 else "bottom",
                           font=dict(color=theme.MUTED, size=11))
    fig.update_layout(title=f"Flow vs. rendimiento del sector · {n} sesiones",
                      xaxis=dict(title="Rendimiento del sector (Select Sector SPDR)", range=[-xr, xr], ticksuffix="%"),
                      yaxis=dict(title="Flow % AUM", range=[-yr, yr], ticksuffix="%"))
    theme.chart(fig, height=460)


def _industries(ctx: Ctx, panel: pd.DataFrame, n: int, table_slot) -> None:
    ind = industry_panel(ctx.flows, ctx.session, n)
    if ind.empty:
        return
    sectors = panel.sort_values("flow_1D", key=lambda s: s.abs().fillna(0), ascending=False)["sector"].tolist()
    pick = st.selectbox("Sector", sectors, format_func=lambda s: SECTOR_ES[s])
    d = ind[ind["sector"] == pick].sort_values(f"flow_{n}D")
    if d.empty:
        st.info("Sin ETFs con datos en este sector.")
        return
    label = [f"{t} · {i}" for t, i in zip(d["ticker"], d["industry"])]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=d[f"flow_{n}D"] / 1e6, y=label, orientation="h", name=f"{n} sesiones",
                         marker_color=theme.sign_color(d[f"flow_{n}D"]), opacity=0.45))
    fig.add_trace(go.Bar(x=d["flow_1D"] / 1e6, y=label, orientation="h", name="Sesión",
                         marker_color=theme.sign_color(d["flow_1D"].fillna(0))))
    fig.update_layout(title=f"{SECTOR_ES[pick]}: flow por ETF ($M) — sesión vs. {n} sesiones",
                      barmode="overlay", yaxis=dict(showgrid=False), legend=dict(orientation="h", y=-0.12))
    theme.chart(fig, height=max(260, 46 * len(d) + 90))
    table_slot.dataframe(pd.DataFrame({
        "ETF": d["ticker"], "Industria": d["industry"],
        "Sesión ($M)": d["flow_1D"] / 1e6, "% AUM": d["pct_1D"] * 100,
        f"{n}D ($M)": d[f"flow_{n}D"] / 1e6, f"{n}D % AUM": d[f"pct_{n}D"] * 100,
        "z": d["z"], "Racha": [_streak_label(s) for s in d["streak"]],
        f"Rend. {n}D": d[f"ret_{n}D"] * 100,
    }).sort_values(f"{n}D ($M)", ascending=False), hide_index=True, width="stretch", column_config={
        "Sesión ($M)": st.column_config.NumberColumn(format="%+.0f"),
        "% AUM": st.column_config.NumberColumn(format="%+.2f%%"),
        f"{n}D ($M)": st.column_config.NumberColumn(format="%+.0f"),
        f"{n}D % AUM": st.column_config.NumberColumn(format="%+.2f%%"),
        "z": st.column_config.NumberColumn(format="%+.1f"),
        f"Rend. {n}D": st.column_config.NumberColumn(format="%+.2f%%"),
    })


def _vanguard_monthly(ctx: Ctx, panel: pd.DataFrame) -> None:
    """Vanguard sector ETFs: month-end flows, and how much of each sector is only visible monthly."""
    m = ctx.monthly
    if m is None or m.empty:
        return
    m = m.assign(sector=m["ticker"].map(sector_of)).dropna(subset=["sector"])
    if m.empty:
        return
    latest = m.sort_values("date").groupby("ticker").tail(1)
    daily_aum = panel.set_index("sector")["aum"]
    t = pd.DataFrame({
        "Sector": latest["sector"].map(SECTOR_ES),
        "ETF": latest["ticker"],
        "Cierre de mes": latest["date"].dt.strftime("%Y-%m-%d"),
        "AUM Vanguard ($B)": latest["aum"] / 1e9,
        "Flow del mes ($M)": latest["flow_usd"] / 1e6,
        "% AUM": latest["flow_pct_aum"] * 100,
        "AUM con dato diario ($B)": latest["sector"].map(daily_aum).values / 1e9,
    })
    t["Cobertura diaria"] = t["AUM con dato diario ($B)"] / (t["AUM con dato diario ($B)"] + t["AUM Vanguard ($B)"]) * 100
    t = t.sort_values("AUM Vanguard ($B)", ascending=False)

    theme.section("Vanguard sectorial · mensual")
    st.caption("Vanguard sólo publica shares a cierre de mes, así que sus ETFs sectoriales no entran a los totales "
               "diarios de arriba. **Cobertura diaria** = parte del AUM sectorial (entre los ETFs del universo) que "
               "sí tiene dato diario; donde es baja, la lectura diaria de ese sector ve menos del dinero institucional.")
    if t["Flow del mes ($M)"].isna().all():
        next_me = (pd.Timestamp(latest["date"].max()) + pd.offsets.MonthEnd(1)).date()
        st.info(f"Primer flow mensual de Vanguard cuando se publique el cierre del {next_me:%d %b %Y}.")
        t = t.drop(columns=["Flow del mes ($M)", "% AUM"])
    st.dataframe(t, hide_index=True, width="stretch", height=36 * len(t) + 40, column_config={
        "AUM Vanguard ($B)": st.column_config.NumberColumn(format="%.1f"),
        "Flow del mes ($M)": st.column_config.NumberColumn(format="%+,.0f"),
        "% AUM": st.column_config.NumberColumn(format="%+.2f%%"),
        "AUM con dato diario ($B)": st.column_config.NumberColumn(format="%.1f"),
        "Cobertura diaria": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
    })


def render(ctx: Ctx) -> None:
    session = sector_session(ctx.flows, ctx.session)
    chips = [(f"sesión {session:%d %b %Y}", "")] if session is not None else []
    if session is not None and session != ctx.session:
        chips.append((f"{ctx.session:%d %b} aún sin datos de SPDR", "warn"))
    theme.header("Sectores", "Dónde están entrando y de dónde están saliendo los institucionales, sector por sector",
                 chips=chips)
    if session is None:
        st.info("Sin una sesión con datos de los 11 sectores todavía.")
        return
    ctx = replace(ctx, session=session)
    sf = with_sector(ctx.flows)
    panel = sector_panel(ctx.flows, ctx.session)
    if panel.empty:
        st.info("Sin datos sectoriales.")
        return
    st.caption("11 sectores GICS. Cada sector suma su Select Sector SPDR, su ETF sectorial de iShares y los ETFs de "
               "industria y temáticos que le pertenecen (p. ej. Financiero = XLF + IYF + KRE + KBE + KIE + IAT + IAI + IAK + IYG + REM). "
               "Vanguard (sólo cierre de mes) va al final. No aplica el filtro de categorías.")

    reading = daily_reading(panel, industry_panel(ctx.flows, ctx.session, 20))
    if reading:
        with st.container(border=True):
            theme.section(f"Lectura de la sesión · {ctx.session:%d %b %Y}")
            # escape "$" so Streamlit doesn't render dollar amounts as LaTeX
            st.markdown("\n".join(f"- {line}" for line in reading).replace("$", r"\$"))

    theme.section("Tablero sectorial")
    _scoreboard(panel)

    a, b = st.columns([2, 3], gap="large")
    with a:
        _bar(panel, ctx.unit)
    with b:
        _heatmap(sf, ctx.session, ctx.unit)

    n = st.segmented_control("Ventana", [5, 20, 60], default=20, format_func=lambda x: f"{x} sesiones",
                             key="sector_window") or 20
    c, d = st.columns([1, 1], gap="large")
    table_slot = st.empty()  # full-width industry table below both charts
    with c:
        _quadrant(panel, n)
    with d:
        theme.section("Industrias dentro del sector")
        _industries(ctx, panel, n, table_slot)

    _vanguard_monthly(ctx, panel)
