"""Data quality tab: per-ticker source, freshness and flags, so stale or broken feeds are visible."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.universe import get_universe
from core.flows_calc import session_coverage
from core.trading_calendar import last_completed_session, trading_days_between

_NO_SOURCE_REASON = {
    "Vanguard": "Sólo publica shares a cierre de mes",
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

    t["lag_sessions"] = [trading_days_between(d, expected) if pd.notna(d) else None for d in t["last_as_of"]]
    t["flags_90d"] = t["flags_90d"].fillna(0).astype(int)

    def health(r):
        if r["status"] == "no_source" or pd.isna(r["source"]):
            return "⚪ sin fuente"
        if r["status"] != "ok":
            return "🔴 falla de fuente"
        if r["lag_sessions"] is not None and r["lag_sessions"] > 2:
            return "🟠 atrasado"
        if r["flags_90d"] > 0:
            return "🟡 con flags"
        return "🟢 ok"

    t["health"] = t.apply(health, axis=1)
    t.loc[t["health"] == "⚪ sin fuente", "detail"] = t["issuer"].map(_NO_SOURCE_REASON).fillna("Sin fuente oficial verificada")
    return t


def render(flows: pd.DataFrame, history: pd.DataFrame, status: pd.DataFrame) -> None:
    st.subheader("Calidad de datos")
    t = build_quality_table(flows, history, status)
    counts = t["health"].value_counts()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Con fuente oficial", f"{(t['health'] != '⚪ sin fuente').sum()}/{len(t)}")
    c2.metric("🟢 OK", int(counts.get("🟢 ok", 0)))
    c3.metric("🟠/🔴 Atrasados o fallando", int(counts.get("🟠 atrasado", 0) + counts.get("🔴 falla de fuente", 0)))
    c4.metric("Sesión esperada", str(last_completed_session().date()))

    st.caption(
        "Cada ETF tiene una sola fuente oficial; si falla, ese día queda vacío (no se rellena con otra fuente). "
        "**Atraso** = sesiones de trading entre el último dato del issuer y la última sesión cerrada. "
        "**Flags** = observaciones excluidas del cálculo (saltos sin confirmar, splits, sin precio) en 90 días."
    )

    health_filter = st.multiselect("Estado", sorted(t["health"].unique()), default=sorted(t["health"].unique()))
    view = t[t["health"].isin(health_filter)].sort_values(["health", "ticker"])
    st.dataframe(
        view[["health", "ticker", "name", "issuer", "source", "last_as_of", "lag_sessions",
              "last_change", "observations", "flags_90d", "as_of_inferred", "detail"]].rename(columns={
            "health": "Estado", "issuer": "Issuer", "source": "Fuente", "last_as_of": "Último as-of",
            "lag_sessions": "Atraso (sesiones)", "last_change": "Último cambio de shares",
            "observations": "Obs.", "flags_90d": "Flags 90d", "as_of_inferred": "Fecha inferida",
            "detail": "Detalle",
        }),
        hide_index=True, width="stretch",
        column_config={
            "Último as-of": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Último cambio de shares": st.column_config.DateColumn(format="YYYY-MM-DD"),
        },
    )

    if flows is not None and not flows.empty:
        cov = session_coverage(flows).tail(60).rename("ETFs").reset_index()
        fig = px.bar(cov, x="date", y="ETFs", title="ETFs con flow válido por sesión (últimas 60)")
        fig.update_layout(height=280, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, width="stretch")
