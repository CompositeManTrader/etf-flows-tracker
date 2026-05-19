"""Issuer-by-issuer scrapers for shares outstanding."""
from __future__ import annotations

from typing import Callable

from config.universe import get_universe

from . import (
    ark, bitwise, fidelity, invesco, ipath, ishares, kraneshares,
    proshares, roboglobal, simplify, spdr, vaneck, vanguard, wisdomtree,
)

_ISSUER_DISPATCH: dict[str, Callable[[str], float | None]] = {
    "iShares": ishares.fetch,
    "BlackRock": ishares.fetch,
    "SPDR": spdr.fetch,
    "State Street": spdr.fetch,
    "ARK": ark.fetch,
    "ProShares": proshares.fetch,
    "Vanguard": vanguard.fetch,
    "VanEck": vaneck.fetch,
    "Invesco": invesco.fetch,
    "KraneShares": kraneshares.fetch,
    "Fidelity": fidelity.fetch,
    "Bitwise": bitwise.fetch,
    "WisdomTree": wisdomtree.fetch,
    "Simplify": simplify.fetch,
    "Barclays": ipath.fetch,
    "ROBO Global": roboglobal.fetch,
}


def try_scrape(ticker: str) -> tuple[float | None, str]:
    universe = get_universe()
    meta = universe.get(ticker, {})
    issuer = meta.get("issuer")
    if not issuer:
        return None, "no_issuer"

    scraper = _ISSUER_DISPATCH.get(issuer)
    if scraper is None:
        return None, f"no_scraper_for_{issuer}"

    try:
        shares = scraper(ticker)
    except Exception as e:  # noqa: BLE001
        return None, f"scraper:{issuer}:error:{type(e).__name__}"

    if shares is None or shares <= 0:
        return None, f"scraper:{issuer}:no_data"
    return float(shares), f"scraper:{issuer}"
