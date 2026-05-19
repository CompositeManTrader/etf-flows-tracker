"""Simplify scraper (SVOL)."""
from __future__ import annotations

from ._http import get_text
from ._parse import find_shares_in_html


def fetch(ticker: str) -> float | None:
    t = ticker.lower()
    urls = [
        f"https://www.simplify.us/etfs/{t}-simplify-volatility-premium-etf" if t == "svol" else None,
        f"https://www.simplify.us/etfs/{t}",
        f"https://simplify.us/etfs/{t}",
    ]
    for url in urls:
        if not url:
            continue
        html = get_text(url)
        if html:
            shares = find_shares_in_html(html)
            if shares:
                return shares
    return None
