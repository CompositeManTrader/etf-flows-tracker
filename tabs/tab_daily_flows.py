"""Daily flows tab: top inflows/outflows + category bar chart for one trading session."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.flows_calc import aggregate_by_category, latest_complete_date, session_coverage, top_movers


def render(flows: pd.DataFrame) -> None:
    st.subheader("Daily Flows")

    f = flows.dropna(subset=["flow_usd", "date"]) if flows is not None and not flows.empty else pd.DataFrame()
    if f.empty:
        st.warning("Aún no hay flows válidos (se necesitan ≥2 sesiones por ETF).")
        return

    cov = session_coverage(f)
    sessions = list(cov.index[::-1][:30])
    default = latest_complete_date(f)
    col_d, col_c, col_n = st.columns([1.2, 3, 1])
    session = col_d.selectbox(
        "Sesión", sessions, index=sessions.index(default) if default in sessions else 0,
        format_func=lambda d: f"{pd.Timestamp(d).date()} · {cov[d]} ETFs",
    )
    cats = sorted(f["category"].dropna().unique().tolist())
    selected_cats = col_c.multiselect("Categorías", cats, default=cats)
    top_n = col_n.number_input("Top N", min_value=5, max_value=50, value=15, step=1)

    day = f[f["date"] == session]
    if selected_cats:
        day = day[day["category"].isin(selected_cats)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Inflows", f"${day.loc[day['flow_usd'] > 0, 'flow_usd'].sum() / 1e9:,.2f}B")
    c2.metric("Total Outflows", f"${day.loc[day['flow_usd'] < 0, 'flow_usd'].sum() / 1e9:,.2f}B")
    c3.metric("Net Flow", f"${day['flow_usd'].sum() / 1e9:,.2f}B")
    c4.metric("ETFs con dato", f"{day['ticker'].nunique()}")
    if session != default:
        st.caption("⚠️ Sesión con cobertura parcial: algunos issuers aún no publican esta fecha.")

    movers = top_movers(day, n=int(top_n), side="both", date=session).assign(
        **{"Flow ($M)": lambda d: (d["flow_usd"] / 1e6).round(1),
           "% AUM": lambda d: (d["flow_pct_aum"] * 100).round(2)}
    )
    cols = ["ticker", "name", "category", "Flow ($M)", "% AUM"]
    left, right = st.columns(2)
    with left:
        st.markdown("**Top Inflows**")
        st.dataframe(movers[movers["flow_usd"] > 0][cols], hide_index=True, width="stretch")
    with right:
        st.markdown("**Top Outflows**")
        st.dataframe(movers[movers["flow_usd"] < 0].sort_values("flow_usd")[cols],
                     hide_index=True, width="stretch")

    agg = aggregate_by_category(day, period_days=1)
    if not agg.empty:
        fig = px.bar(
            agg.sort_values("flow_usd_b"),
            x="flow_usd_b", y="category", orientation="h",
            color="flow_usd_b", color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
            labels={"flow_usd_b": "Flow ($B)", "category": ""},
            title=f"Net Flows por Categoría — {pd.Timestamp(session).date()}",
        )
        fig.update_layout(height=max(300, 28 * len(agg)))
        st.plotly_chart(fig, width="stretch")

    with st.expander("Tabla completa"):
        st.dataframe(day.sort_values("flow_usd", ascending=False), hide_index=True, width="stretch")
        st.download_button(
            "Descargar CSV",
            day.to_csv(index=False).encode("utf-8"),
            file_name=f"etf_flows_{pd.Timestamp(session).date()}.csv",
            mime="text/csv",
        )
