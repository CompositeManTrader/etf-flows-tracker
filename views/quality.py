"""Data quality: per-ticker source, freshness and flags, so stale or broken feeds are visible."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.universe import get_universe
from core.flows_calc import session_coverage
from core.trading_calendar import last_completed_session, trading_days_between
from ui import theme

_NO_SOURCE_REASON = {
    "Vanguard": "Sólo publica shares a cierre de mes · ver página Vanguard mensual",
    "ARK": "Página renderizada con JS",
    "VanEck": "Página renderizada con JS",
    "WisdomTree": "Bloquea acceso automatizado (403)",
    "Fidelity": "Página renderizada con JS",
}


def build_quality_table(flows: pd.DataFrame, history: pd.DataFrame, status: pd.DataFrame) -> pd.DataFrame:
    expected = last_completed_session()
    uni = pd.DataFrame.from_dict(get_universe(), orient="index").rename_axis("ticker").reset_index()

    h = history.groupby("ticker").agg(
        last_as_of=("as_of_date", "max"), observations=("as_of_date", "size"),
        as_of_inferred=("as_of_inferred", "last"),
    ).reset_index() if not history.empty else pd.DataFrame(columns=["ticker"])

    if flows is not None and not flows.empty:
        changed = flows[flows["delta_shares"].fillna(0) != 0].groupby("ticker")["date"].max().rename("last_change")
        recent = flows[flows["date"] >= flows["date"].max() - pd.Timedelta(days=90)]
        flags = recent[~recent["quality"].isin(["ok", "first"])].groupby("ticker").size().rename("flags_90d")
        q = pd.concat([changed, flags], axis=1).reset_index().rename(columns={"index": "ticker"})
    else:
        q = pd.DataFrame(columns=["ticker", "last_change", "flags_90d"])

    st_cols = status[["ticker", "source", "status", "detail"]] if not status.empty else \
        pd.DataFrame(columns=["ticker", "source", "status", "detail"])
    t = uni.merge(st_cols, on="ticker", how="left").merge(h, on="ticker", how="left").merge(q, on="ticker", how="left")

    t["lag_sessions"] = [trading_days_between(d, expected) if pd.notna(d) else float("nan") for d in t["last_as_of"]]
    t["flags_90d"] = t["flags_90d"].fillna(0).astype(int)

    def health(r):
        if r["status"] == "no_source" or pd.isna(r["source"]):
            return "⚪ sin fuente"
        if r["status"] != "ok":
            return "🔴 falla de fuente"
        if r["lag_sessions"] > 2:
            return "🟠 atrasado"
        if r["flags_90d"] > 0:
            return "🟡 con flags"
        return "🟢 ok"

    t["health"] = t.apply(health, axis=1)
    t.loc[t["health"] == "⚪ sin fuente", "detail"] = t["issuer"].map(_NO_SOURCE_REASON).fillna("Sin fuente oficial verificada")
    return t


def render(ctx) -> None:
    flows, history, status = ctx.flows, ctx.history, ctx.status
    theme.header("Calidad de datos", "Fuente, frescura y controles de cada ETF del universo")
    t = build_quality_table(flows, history, status)
    counts = t["health"].value_counts()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Con fuente oficial diaria", f"{(t['health'] != '⚪ sin fuente').sum()}/{len(t)}", border=True)
    c2.metric("OK", int(counts.get("🟢 ok", 0)), border=True)
    c3.metric("Atrasados o fallando", int(counts.get("🟠 atrasado", 0) + counts.get("🔴 falla de fuente", 0)),
              border=True)
    c4.metric("Sesión esperada", f"{last_completed_session():%d %b %Y}", border=True)

    st.caption(
        "Cada ETF tiene una sola fuente oficial; si falla, ese día queda vacío (no se rellena con otra fuente). "
        "**Atraso** = sesiones de trading entre el último dato del issuer y la última sesión cerrada. "
        "**Flags** = observaciones excluidas del cálculo (saltos sin confirmar, splits, sin precio) en 90 días."
    )

    severity = ["🔴 falla de fuente", "🟠 atrasado", "🟡 con flags", "🟢 ok", "⚪ sin fuente"]
    present = [s for s in severity if s in set(t["health"])]
    health_filter = st.pills("Estado", present, selection_mode="multi", default=present)
    view = t[t["health"].isin(health_filter or present)].copy()
    view["rank"] = view["health"].map(severity.index)
    view = view.sort_values(["rank", "ticker"])
    view["source"] = view["source"].fillna("—")
    view["detail"] = view["detail"].fillna("")
    view["as_of_inferred"] = view["as_of_inferred"].map({True: "sí"}).fillna("")
    # Streamlit renders missing dates as "None"; show them as blank text instead
    for c in ("last_as_of", "last_change"):
        view[c] = pd.to_datetime(view[c]).dt.strftime("%Y-%m-%d").fillna("")
    st.dataframe(
        view[["health", "ticker", "name", "issuer", "source", "last_as_of", "lag_sessions",
              "last_change", "observations", "flags_90d", "as_of_inferred", "detail"]].rename(columns={
            "health": "Estado", "ticker": "ETF", "name": "Nombre", "issuer": "Issuer", "source": "Fuente",
            "last_as_of": "Último as-of", "lag_sessions": "Atraso", "last_change": "Último cambio",
            "observations": "Obs.", "flags_90d": "Flags 90d", "as_of_inferred": "Fecha inferida",
            "detail": "Detalle",
        }),
        hide_index=True, width="stretch", height=520,
        column_config={
            "Último cambio": st.column_config.TextColumn(help="Última sesión con Δshares ≠ 0"),
            "Atraso": st.column_config.NumberColumn(format="%d", help="Sesiones entre el último dato y la última sesión cerrada"),
            "Obs.": st.column_config.NumberColumn(format="%d"),
        },
    )

    if flows is not None and not flows.empty:
        cov = session_coverage(flows).tail(60).rename("ETFs").reset_index()
        fig = px.bar(cov, x="date", y="ETFs", title="ETFs con flow válido por sesión (últimas 60)")
        fig.update_traces(marker_color=theme.ACCENT)
        fig.update_layout(xaxis_title="", yaxis_title="", xaxis=dict(rangebreaks=theme.TRADING_RANGEBREAKS))
        theme.chart(fig, height=280)
