"""Vanguard scraper.

Strategy: Vanguard's product pages are SPAs but hydrate with embedded JSON.
Also try their internal-but-public IRE (Investment Research Enterprise) API.
"""
from __future__ import annotations

from ._http import get_text
from ._parse import find_shares_in_html


def fetch(ticker: str) -> float | None:
    t = ticker.lower()
    urls = [
        # Internal JSON often used by their site
        f"https://api.vanguard.com/rs/ire/01/ind/fund/{t.upper()}/profile.json",
        f"https://personal1.vanguard.com/rs/gre/gra/datasets/auw-retail-fund-overview.jsonp"
        f"?reqFundIds={t.upper()}",
        # Product pages with embedded JSON
        f"https://investor.vanguard.com/investment-products/etfs/profile/{t}",
        f"https://advisors.vanguard.com/investments/products/{t}/",
        f"https://institutional.vanguard.com/investments/product-details/fund/{t}",
    ]
    for url in urls:
        text = get_text(url)
        if not text:
            continue
        shares = find_shares_in_html(text)
        if shares:
            return shares
    return None
