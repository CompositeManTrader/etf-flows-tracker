"""ProShares scraper.

Strategy: try a couple of product-page URL patterns and parse HTML for
"Shares Outstanding".
"""
from __future__ import annotations

import re

from ._http import get_text

_CATEGORIES = ("strategic", "leveraged-and-inverse", "esg", "thematic", "core")


def _parse(html: str) -> float | None:
    if not html:
        return None
    patterns = [
        r"Shares\s+Outstanding[^0-9]{1,80}([\d,\.]+)\s*(M|Million|B|Billion)?",
        r"Number\s+of\s+Shares[^0-9]{1,80}([\d,\.]+)\s*(M|Million|B|Billion)?",
        r'"sharesOutstanding"\s*:\s*"?([\d,\.]+)"?',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if not m:
            continue
        try:
            num = float(m.group(1).replace(",", "").strip())
        except ValueError:
            continue
        suffix = (m.group(2) or "").upper() if m.lastindex and m.lastindex >= 2 else ""
        if suffix.startswith("M"):
            num *= 1_000_000
        elif suffix.startswith("B"):
            num *= 1_000_000_000
        if num > 0:
            return num
    return None


def fetch(ticker: str) -> float | None:
    t = ticker.lower()
    urls = [f"https://finance.proshares.com/funds/{t}.html"]
    for cat in _CATEGORIES:
        urls.append(f"https://www.proshares.com/our-etfs/{cat}/{t}")
    for url in urls:
        html = get_text(url)
        if html:
            shares = _parse(html)
            if shares:
                return shares
    return None
