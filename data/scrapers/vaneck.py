"""VanEck scraper.

Strategy: each ETF has a page at
  https://www.vaneck.com/us/en/investments/{slug}/overview/

Scrape HTML for "Shares Outstanding".
"""
from __future__ import annotations

import re

from ._http import get_text

_SLUGS = {
    "SMH": "semiconductor-etf-smh",
    "MOAT": "morningstar-wide-moat-etf-moat",
    "EMLC": "jp-morgan-em-local-currency-bond-etf-emlc",
}


def _parse(html: str) -> float | None:
    if not html:
        return None
    m = re.search(
        r"Shares\s+Outstanding[^0-9]{1,80}([\d,\.]+)\s*(M|Million|B|Billion)?",
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
    return num if num > 0 else None


def fetch(ticker: str) -> float | None:
    slug = _SLUGS.get(ticker.upper())
    candidates = []
    if slug:
        candidates.append(f"https://www.vaneck.com/us/en/investments/{slug}/overview/")
    # fallback: try by ticker
    candidates.append(f"https://www.vaneck.com/us/en/investments/{ticker.lower()}/")
    for url in candidates:
        html = get_text(url)
        if html:
            shares = _parse(html)
            if shares:
                return shares
    return None
