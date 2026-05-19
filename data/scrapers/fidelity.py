"""Fidelity scraper (FBTC, Wise Origin Bitcoin Fund)."""
from __future__ import annotations

from ._http import get_text
from ._parse import find_shares_in_html


def fetch(ticker: str) -> float | None:
    t = ticker.upper()
    urls = [
        f"https://institutional.fidelity.com/app/funds-and-products/{t}/",
        f"https://www.fidelity.com/etfs/summary/{t}",
        f"https://fundresearch.fidelity.com/etfs/snapshot/{t}",
    ]
    for url in urls:
        html = get_text(url)
        if html:
            shares = find_shares_in_html(html)
            if shares:
                return shares
    return None
