"""ProShares scraper."""
from __future__ import annotations

from ._http import get_text
from ._parse import find_shares_in_html

_CATEGORIES = ("strategic", "leveraged-and-inverse", "esg", "thematic", "core")


def fetch(ticker: str) -> float | None:
    t = ticker.lower()
    urls = [
        f"https://finance.proshares.com/funds/{t}.html",
        f"https://finance.proshares.com/funds/{t}",
    ]
    for cat in _CATEGORIES:
        urls.append(f"https://www.proshares.com/our-etfs/{cat}/{t}")
        urls.append(f"https://www.proshares.com/our-etfs/{cat}/{t}/")
    for url in urls:
        html = get_text(url)
        if not html:
            continue
        shares = find_shares_in_html(html)
        if shares:
            return shares
    return None
