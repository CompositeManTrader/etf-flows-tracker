"""Bitwise scraper (BITB)."""
from __future__ import annotations

from ._http import get_text
from ._parse import find_shares_in_html


def fetch(ticker: str) -> float | None:
    t = ticker.lower()
    urls = [
        f"https://bitbetf.com/",  # BITB has its own microsite
        f"https://www.bitwiseinvestments.com/funds/{t}",
        f"https://www.bitwiseinvestments.com/etfs/{t}",
    ]
    for url in urls:
        html = get_text(url)
        if html:
            shares = find_shares_in_html(html)
            if shares:
                return shares
    return None
