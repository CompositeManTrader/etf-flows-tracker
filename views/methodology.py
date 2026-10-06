"""How the numbers are built and what they can't tell you."""
from __future__ import annotations

import streamlit as st

from ui import theme


def render(ctx) -> None:
    theme.header("Metodología", "Cómo se calcula cada número y cuáles son sus límites")
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("""
#### Qué mide
Cuando un inversor institucional compra o vende un ETF en volumen, un *authorized participant* **crea o
redime shares** con el issuer. El cambio diario en shares outstanding es, por lo tanto, la huella directa
del dinero que entra o sale del fondo — no la compraventa entre inversores en el mercado secundario.

#### Fórmula
- **Flow** = (Shares hoy − Shares sesión previa) × NAV de hoy
- **% AUM** = Flow ÷ (Shares previas × NAV previo)
- **z-score** = flow % AUM vs. la media y desviación de las últimas 60 sesiones del mismo ETF

#### Fuentes (oficiales, una por ETF)
SPDR (archivo NAV histórico), iShares (página del fondo), Invesco (API de precios), ProShares (CSV histórico),
KraneShares, Simplify y Bitwise (página del fondo). Precios y volumen de mercado: yfinance.
Vanguard sólo publica shares a fin de mes → página aparte.
""")
    with b:
        st.markdown("""
#### Controles de calidad
Un flow sólo cuenta si pasa todos:
- Valor ≥ 100k shares y sin picos aislados
- Saltos > 15% confirmados por la siguiente publicación (si no: *pending/suspect*)
- Splits detectados (shares × precio sin cambio) y excluidos
- NAV a ≤ 5% del cierre de mercado (si no: fondo mal mapeado)
- Si una fuente falla, el día queda vacío — **nunca** se rellena con otra fuente

#### Lectura y límites
- Los issuers publican con distinto rezago; los rankings usan la **última sesión completa**.
- Un flow refleja órdenes de creación del día; puede ser de un solo cliente grande.
- Flows de ETFs apalancados/inversos y de volatilidad se leen al revés en términos de riesgo.
- 22 ETFs no tienen fuente diaria verificada (Vanguard, ARK, VanEck…). El volumen relativo los cubre como proxy.
- No es asesoría de inversión.
""")
