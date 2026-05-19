"""WisdomTree scraper (HEDJ)."""
from __future__ import annotations

from ._http import get_text
from ._parse import find_shares_in_html

_SLUGS = {
    "HEDJ": "europe-hedged-equity-fund",
}


def fetch(ticker: str) -> float | None:
    t = ticker.lower()
    slug = _SLUGS.get(ticker.upper())
    urls = []
    if slug:
        urls.append(f"https://www.wisdomtree.com/investments/etfs/equity/{slug}")
    urls.append(f"https://www.wisdomtree.com/investments/etfs/{t}")
    urls.append(f"https://www.wisdomtree.com/{t}")
    for url in urls:
        html = get_text(url)
        if html:
            shares = find_shares_in_html(html)
            if shares:
                return shares
    return None
