"""Daily flows tab: top inflows/outflows + category bar chart."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.flows_calc import aggregate_by_category, top_movers


def render(flows: pd.DataFrame) -> None:
    st.subheader("Daily Flows")

    if flows is None or flows.empty:
        st.warning("No hay flows todavía. Corre `python jobs/daily_snapshot.py` al menos 2 días para empezar a ver deltas.")
        return

    f = flows.dropna(subset=["flow_usd", "date"]).copy()
    if f.empty:
        st.warning("Aún no hay deltas calculables (se necesitan ≥2 snapshots).")
        return

    last_date = f["date"].max()
    today = f[f["date"] == last_date]

    inflows_total = today.loc[today["flow_usd"] > 0, "flow_usd"].sum() / 1e9
    outflows_total = today.loc[today["flow_usd"] < 0, "flow_usd"].sum() / 1e9
    net = today["flow_usd"].sum() / 1e9

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Inflows", f"${inflows_total:,.2f}B")
    c2.metric("Total Outflows", f"${outflows_total:,.2f}B")
    c3.metric("Net Flow", f"${net:,.2f}B")

    st.caption(f"Última fecha: {pd.Timestamp(last_date).date()}")

    cats = sorted(f["category"].dropna().unique().tolist())
    col_a, col_b = st.columns([3, 1])
    selected_cats = col_a.multiselect("Categorías", cats, default=cats)
    top_n = col_b.number_input("Top N", min_value=5, max_value=50, value=15, step=1)

    today_f = today[today["category"].isin(selected_cats)] if selected_cats else today

    movers = top_movers(today_f, n=int(top_n), side="both")
    inflow_tbl = movers[movers["flow_usd"] > 0].copy()
    outflow_tbl = movers[movers["flow_usd"] < 0].copy()

    for tbl in (inflow_tbl, outflow_tbl):
        tbl["Flow ($M)"] = (tbl["flow_usd"] / 1e6).round(1)

    left, right = st.columns(2)
    with left:
        st.markdown("**Top Inflows**")
        st.dataframe(
            inflow_tbl[["ticker", "name", "category", "Flow ($M)"]],
            hide_index=True, use_container_width=True,
        )
    with right:
        st.markdown("**Top Outflows**")
        st.dataframe(
            outflow_tbl[["ticker", "name", "category", "Flow ($M)"]],
            hide_index=True, use_container_width=True,
        )

    agg = aggregate_by_category(today_f, period_days=1)
    if not agg.empty:
        fig = px.bar(
            agg.sort_values("flow_usd_b"),
            x="flow_usd_b", y="category",
            orientation="h",
            color="flow_usd_b",
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            labels={"flow_usd_b": "Flow ($B)", "category": ""},
            title="Net Flows por Categoría — último día",
        )
        fig.update_layout(height=max(300, 28 * len(agg)))
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Tabla completa"):
        st.dataframe(today_f.sort_values("flow_usd", ascending=False), hide_index=True, use_container_width=True)
        csv = today_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Descargar CSV",
            csv,
            file_name=f"etf_flows_{pd.Timestamp(last_date).date()}.csv",
            mime="text/csv",
        )
