"""ARK Invest scraper.

Strategy: scrape the per-fund product page HTML at
  https://ark-funds.com/funds/{ticker_lower}/

Look for shares outstanding in HTML (usually in a Fund Statistics table or
JSON-LD block).
"""
from __future__ import annotations

import json
import re

from ._http import get_text


def _parse_shares(html: str) -> float | None:
    if not html:
        return None

    # Try JSON-LD blocks first (cleaner)
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE,
    ):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            for key in ("sharesOutstanding", "totalShares"):
                if key in item:
                    val = _to_num(item[key])
                    if val:
                        return val

    # Plain-text patterns
    patterns = [
        r"Shares\s+Outstanding[^0-9]{1,80}([\d,\.]+)\s*(M|Million|B|Billion)?",
        r'"sharesOutstanding"\s*:\s*"?([\d,\.]+)"?',
        r"Total\s+Shares[^0-9]{1,40}([\d,\.]+)\s*(M|Million)?",
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if not m:
            continue
        num = _to_num(m.group(1))
        if num is None:
            continue
        suffix = (m.group(2) or "").upper() if m.lastindex and m.lastindex >= 2 else ""
        if suffix.startswith("M"):
            num *= 1_000_000
        elif suffix.startswith("B"):
            num *= 1_000_000_000
        if num > 0:
            return num
    return None


def _to_num(v) -> float | None:
    try:
        return float(str(v).replace(",", "").strip())
    except (ValueError, AttributeError, TypeError):
        return None


def fetch(ticker: str) -> float | None:
    for url in (
        f"https://ark-funds.com/funds/{ticker.lower()}/",
        f"https://www.ark-funds.com/funds/{ticker.lower()}/",
    ):
        html = get_text(url)
        if html:
            shares = _parse_shares(html)
            if shares:
                return shares
    return None
