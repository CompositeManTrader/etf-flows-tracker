"""ROBO Global scraper (ROBO ETF).

ROBO Global is the index provider; the ETF is issued by Exchange Traded
Concepts. Their product page is at roboglobaletfs.com.
"""
from __future__ import annotations

from ._http import get_text
from ._parse import find_shares_in_html


def fetch(ticker: str) -> float | None:
    t = ticker.lower()
    urls = [
        f"https://www.roboglobaletfs.com/{t}",
        f"https://roboglobaletfs.com/{t}",
        f"https://www.roboglobal.com/etfs/{t}",
    ]
    for url in urls:
        html = get_text(url)
        if html:
            shares = find_shares_in_html(html)
            if shares:
                return shares
    return None
