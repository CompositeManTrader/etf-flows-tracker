"""Morning brief tab: Groq-powered narrative summary."""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from core.flows_calc import aggregate_by_category, detect_rotation, top_movers

_MODEL = "llama-3.3-70b-versatile"


def _build_prompt(flows: pd.DataFrame) -> str:
    if flows is None or flows.empty:
        return "Sin datos de flows disponibles."

    last_date = flows["date"].max()
    today = flows[flows["date"] == last_date]

    inflows = top_movers(today, n=10, side="inflow")[["ticker", "name", "category", "flow_usd"]]
    outflows = top_movers(today, n=10, side="outflow")[["ticker", "name", "category", "flow_usd"]]
    cats = aggregate_by_category(flows, period_days=1)
    rot = detect_rotation(flows, short=5, long=20).head(5)

    def _fmt_table(df: pd.DataFrame, value_col: str = "flow_usd") -> str:
        if df.empty:
            return "(sin datos)"
        d = df.copy()
        d[value_col] = (d[value_col] / 1e6).round(1)
        return d.to_string(index=False)

    parts = [
        f"Fecha: {pd.Timestamp(last_date).date()}",
        "",
        "Eres un analista de mercado institucional. Redacta un brief matinal en español, máximo 250 palabras, "
        "tono profesional y sin emojis. Estructura:",
        "1. Resumen ejecutivo (2-3 líneas)",
        "2. Categorías destacadas (mayores entradas y salidas)",
        "3. Rotación detectada (5D vs 20D)",
        "4. Lectura de mercado: risk-on / risk-off / neutral, justificando con los datos",
        "",
        f"Top 10 inflows ($M):\n{_fmt_table(inflows)}",
        "",
        f"Top 10 outflows ($M):\n{_fmt_table(outflows)}",
        "",
        f"Net flow por categoría ($B):\n{cats[['category', 'flow_usd_b']].round(2).to_string(index=False) if not cats.empty else '(sin datos)'}",
        "",
        f"Top 5 rotación 5D vs 20D ($B):\n{rot[['category', 'rotation_b']].round(2).to_string(index=False) if not rot.empty else '(sin datos)'}",
    ]
    return "\n".join(parts)


def _get_api_key() -> str | None:
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GROQ_API_KEY")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return None


def render(flows: pd.DataFrame) -> None:
    st.subheader("Morning Brief")

    if flows is None or flows.empty:
        st.warning("No hay flows para resumir.")
        return

    prompt = _build_prompt(flows)
    api_key = _get_api_key()

    if not api_key:
        st.info("No se detectó `GROQ_API_KEY`. Configúrala en `st.secrets` o variable de entorno. Mientras tanto, copia el prompt a la mano:")
        with st.expander("Prompt para LLM"):
            st.code(prompt)
        return

    if st.button("Generar brief"):
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                model=_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=600,
            )
            text = resp.choices[0].message.content
            st.markdown(text)
        except Exception as e:  # noqa: BLE001
            st.error(f"Error llamando a Groq: {type(e).__name__}: {e}")

    with st.expander("Ver prompt enviado"):
        st.code(prompt)
