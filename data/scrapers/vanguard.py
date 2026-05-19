"""Vanguard scraper.

Strategy: hit the public profile snapshot API:
  https://investor.vanguard.com/investment-products/etfs/profile/api/{ticker}/profile/snapshot

Returns JSON with `sharesOutstanding`. Falls back to HTML product page.
"""
from __future__ import annotations

import json
import re

from ._http import get_text


def _from_json(payload: str) -> float | None:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    # walk dict looking for sharesOutstanding-ish keys
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    stack.append(v)
                else:
                    kl = str(k).lower()
                    if "sharesoutstanding" in kl or kl == "shares":
                        try:
                            n = float(str(v).replace(",", ""))
                            if n > 0:
                                return n
                        except (ValueError, TypeError):
                            continue
        elif isinstance(node, list):
            stack.extend(node)
    return None


def _from_html(html: str) -> float | None:
    if not html:
        return None
    m = re.search(
        r"Shares\s+outstanding[^0-9]{1,80}([\d,\.]+)\s*(M|Million|B|Billion)?",
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
    t = ticker.lower()
    api_url = (
        f"https://investor.vanguard.com/investment-products/etfs/profile/api/"
        f"{t}/profile/snapshot"
    )
    payload = get_text(api_url)
    if payload:
        n = _from_json(payload)
        if n:
            return n

    html = get_text(f"https://investor.vanguard.com/investment-products/etfs/profile/{t}")
    return _from_html(html or "")
