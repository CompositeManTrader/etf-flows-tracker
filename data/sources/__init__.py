"""Official shares-outstanding sources. Exactly one source per ticker, no fallbacks.

Mixing sources was the main defect of v1: when one source failed and another
filled in, the day-over-day delta compared two different numbers and produced
billion-dollar phantom flows. A ticker whose source fails simply has no row
for that session.
"""
from __future__ import annotations

from typing import Callable

import pandas as pd

from config.universe import get_universe

from . import ishares, pages, proshares, spdr

_BY_ISSUER: dict[str, tuple[str, Callable[[str], pd.DataFrame]]] = {
    "SPDR": ("spdr_navhist", spdr.fetch),
    "ProShares": ("proshares_navcsv", proshares.fetch),
}

# Issuers checked and found unusable (Oct 2026): Vanguard publishes only monthly
# assets; ARK, VanEck, Invesco, WisdomTree, Fidelity render via JS or block bots.


def source_for(ticker: str) -> tuple[str, Callable[[str], pd.DataFrame]] | None:
    t = ticker.upper()
    if t in pages.PAGES:
        return "issuer_page", pages.fetch
    if t in ishares.PRODUCTS:
        return "ishares_page", ishares.fetch
    issuer = get_universe().get(t, {}).get("issuer")
    return _BY_ISSUER.get(issuer)


def source_map() -> dict[str, str | None]:
    """ticker -> source name (None = no reliable source)."""
    return {t: (s[0] if (s := source_for(t)) else None) for t in get_universe()}
