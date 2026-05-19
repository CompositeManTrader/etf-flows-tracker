"""Issuer-by-issuer scrapers for shares outstanding.

Each scraper exposes `fetch(ticker: str) -> float | None`. Returns None on
any failure (network, parse, missing field). The dispatcher `try_scrape`
routes a ticker to the right scraper based on the `issuer` field in the
ETF universe.
"""
from __future__ import annotations

from typing import Callable

from config.universe import get_universe

from . import ark, invesco, ishares, proshares, spdr, vaneck, vanguard

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
}


def try_scrape(ticker: str) -> tuple[float | None, str]:
    """Look up issuer in universe and call the matching scraper.

    Returns (shares, source_label). source_label is "scraper:{issuer}" on
    success, "no_scraper" if there's no scraper for that issuer, or
    "scraper:{issuer}:failed" on failure.
    """
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
