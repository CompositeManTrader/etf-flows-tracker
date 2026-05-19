"""iPath / Barclays scraper (VXX)."""
from __future__ import annotations

from ._http import get_text
from ._parse import find_shares_in_html


def fetch(ticker: str) -> float | None:
    t = ticker.upper()
    urls = [
        f"https://www.ipathetn.barclays/details.app?instrumentId=341408&ticker={t}",
        f"https://www.ipathetn.barclays/ticker/{t}",
        f"https://ipathetn.com/US/16/en/details.app?instrumentId={t}",
    ]
    for url in urls:
        html = get_text(url)
        if html:
            shares = find_shares_in_html(html)
            if shares:
                return shares
    return None
