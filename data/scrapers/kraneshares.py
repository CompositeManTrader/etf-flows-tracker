"""KraneShares scraper (KWEB)."""
from __future__ import annotations

from ._http import get_text
from ._parse import find_shares_in_html


def fetch(ticker: str) -> float | None:
    t = ticker.lower()
    for url in (
        f"https://kraneshares.com/{t}/",
        f"https://kraneshares.com/funds/{t}/",
        f"https://kraneshares.com/{t}",
    ):
        html = get_text(url)
        if html:
            shares = find_shares_in_html(html)
            if shares:
                return shares
    return None
