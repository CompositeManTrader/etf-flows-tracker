"""Invesco scraper.

Invesco product pages live at:
  https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker={TICKER}

They expose fund stats in HTML. Scrape "Shares Outstanding".
"""
from __future__ import annotations

import re

from ._http import get_text


def _parse(html: str) -> float | None:
    if not html:
        return None
    m = re.search(
        r"Shares\s+Outstanding[^0-9\-]{1,120}([\d,\.]+)\s*(M|Million|B|Billion)?",
        html, re.IGNORECASE,
    )
    if not m:
        return None
    try:
        num = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    suffix = (m.group(2) or "").upper() if m.lastindex and m.lastindex >= 2 else ""
    if suffix.startswith("M"):
        num *= 1_000_000
    elif suffix.startswith("B"):
        num *= 1_000_000_000
    return num if num > 100_000 else None


def fetch(ticker: str) -> float | None:
    t = ticker.upper()
    urls = [
        f"https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker={t}",
        f"https://www.invesco.com/qqq-etf/en/about.html" if t == "QQQ" else None,
    ]
    for url in urls:
        if not url:
            continue
        html = get_text(url)
        if html:
            shares = _parse(html)
            if shares:
                return shares
    return None
