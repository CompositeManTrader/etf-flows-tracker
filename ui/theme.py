"""Visual system: colour tokens, Plotly template, CSS and number formatting."""
from __future__ import annotations

import math

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

POS = "#2FBF71"      # inflow
NEG = "#E5484D"      # outflow
NEUTRAL = "#64748B"
ACCENT = "#4C8DFF"
TEXT = "#E2E8F0"
MUTED = "#8A9BB0"
GRID = "rgba(138,155,176,0.14)"
SURFACE = "#111A24"
BORDER = "#1E2A38"

# diverging scale centred on the surface colour, so ~0 fades into the card
DIVERGING = [[0.0, "#B4232A"], [0.25, NEG], [0.5, SURFACE], [0.75, POS], [1.0, "#1A8A4E"]]
CATEGORY_COLORS = ["#4C8DFF", "#F5A524", "#2FBF71", "#A78BFA", "#22D3EE", "#F472B6", "#E5484D",
                   "#FACC15", "#94A3B8", "#FB923C", "#34D399", "#818CF8", "#F87171", "#C084FC"]

_CSS = """
<style>
.block-container {padding-top: 2.2rem; padding-bottom: 2rem; max-width: 1480px;}
h1, h2, h3 {letter-spacing: -0.015em;}
[data-testid="stMetricValue"] {font-variant-numeric: tabular-nums; font-size: 1.55rem;}
[data-testid="stMetricLabel"] p {color: #8A9BB0; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em;}
.desk-sub {color: #8A9BB0; font-size: 0.9rem; margin-top: -0.6rem; margin-bottom: 1.1rem;}
.desk-chip {display: inline-block; padding: 1px 9px; margin-right: 6px; border-radius: 999px;
            border: 1px solid #1E2A38; background: #111A24; color: #CBD5E1; font-size: 0.78rem;}
.desk-chip.pos {color: #2FBF71; border-color: rgba(47,191,113,.35);}
.desk-chip.neg {color: #E5484D; border-color: rgba(229,72,77,.35);}
.desk-chip.warn {color: #F5A524; border-color: rgba(245,165,36,.35);}
.desk-brand {font-weight: 700; font-size: 1.05rem; letter-spacing: -0.01em;}
.desk-brand span {color: #4C8DFF;}
.desk-section {color: #8A9BB0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em;
               margin: 0.4rem 0 0.2rem 0;}
</style>
"""


def apply() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    pio.templates["desk"] = go.layout.Template(layout=dict(
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, sans-serif", size=12, color=TEXT),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=CATEGORY_COLORS,
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=BORDER, tickfont=dict(color=MUTED),
                   automargin=True),
        yaxis=dict(gridcolor=GRID, zerolinecolor="rgba(138,155,176,0.35)", linecolor=BORDER,
                   tickfont=dict(color=MUTED), automargin=True),
        margin=dict(l=8, r=8, t=36, b=8),
        title=dict(font=dict(size=13, color=TEXT), x=0, xanchor="left"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED), orientation="h", y=-0.15),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(color=TEXT)),
        coloraxis=dict(colorbar=dict(outlinewidth=0, tickfont=dict(color=MUTED), thickness=10)),
    ))
    pio.templates.default = "desk"


TRADING_RANGEBREAKS = [dict(bounds=["sat", "mon"])]  # hide weekends on date axes


def padded_range(values, pad: float = 0.35) -> list[float]:
    """x-range with room for outside bar labels on both sides."""
    lo, hi = min(0.0, float(min(values))), max(0.0, float(max(values)))
    span = (hi - lo) or 1.0
    return [lo - span * pad * (lo < 0), hi + span * pad * (hi > 0)]


def chart(fig, height: int | None = None) -> None:
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def header(title: str, subtitle: str = "", chips: list[tuple[str, str]] | None = None) -> None:
    st.markdown(f"## {title}")
    chip_html = "".join(f'<span class="desk-chip {cls}">{txt}</span>' for txt, cls in (chips or []))
    if subtitle or chip_html:
        st.markdown(f'<div class="desk-sub">{chip_html}{subtitle}</div>', unsafe_allow_html=True)


def section(label: str) -> None:
    st.markdown(f'<div class="desk-section">{label}</div>', unsafe_allow_html=True)


def usd(x, signed: bool = True) -> str:
    """$1.28B / -$845M / +$12M."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    sign = ("+" if x > 0 else "-" if x < 0 else "") if signed else ("-" if x < 0 else "")
    a = abs(x)
    if a >= 1e12:
        body = f"{a / 1e12:.2f}T"
    elif a >= 1e9:
        body = f"{a / 1e9:.2f}B"
    elif a >= 1e6:
        body = f"{a / 1e6:.0f}M"
    elif a >= 1e3:
        body = f"{a / 1e3:.0f}K"
    else:
        body = f"{a:.0f}"
    return f"{sign}${body}"


def pct(x, digits: int = 2, signed: bool = True) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{x * 100:+.{digits}f}%" if signed else f"{x * 100:.{digits}f}%"


def sign_color(values) -> list[str]:
    return [POS if (v or 0) >= 0 else NEG for v in values]
