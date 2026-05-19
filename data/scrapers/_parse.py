"""Shared HTML/JSON parser to find shares outstanding.

Most issuer SPAs hydrate the page by embedding a JSON blob inside a
<script> tag. This module tries (in order):
  1. JSON-LD application/ld+json blocks
  2. Common embedded JSON patterns: window.__NEXT_DATA__, __PRELOADED_STATE__, etc.
  3. Generic regex for "sharesOutstanding": NUM or "Shares Outstanding ... NUM"
"""
from __future__ import annotations

import json
import re

_SHARES_KEY_RE = re.compile(
    r'"(sharesOutstanding|totalSharesOutstanding|numberOfShares|fundSharesOutstanding|sharesOuts)"'
    r'\s*:\s*"?([\d,\.eE+-]+)"?',
    re.IGNORECASE,
)

_TEXT_RE = re.compile(
    r"(?:Shares?\s+Outstanding|Total\s+Shares|Number\s+of\s+Shares)"
    r"[^0-9]{1,200}?([\d][\d,\.]*)\s*(M|MM|Million|B|Billion|K|Thousand)?",
    re.IGNORECASE | re.DOTALL,
)


def _coerce(num: str, suffix: str = "") -> float | None:
    try:
        n = float(num.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None
    s = (suffix or "").upper()
    if s.startswith("K") or s == "THOUSAND":
        n *= 1_000
    elif s in ("M", "MM") or s.startswith("MILLION"):
        n *= 1_000_000
    elif s.startswith("B") or s == "BILLION":
        n *= 1_000_000_000
    return n if n > 100_000 else None


def find_shares_in_html(html: str) -> float | None:
    """Try multiple strategies; return first plausible value (> 100k)."""
    if not html:
        return None

    # 1. JSON-LD blocks
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE,
    ):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        n = _walk_json_for_shares(data)
        if n:
            return n

    # 2. Embedded JSON in known hydration scripts
    for pat in (
        r"window\.__NEXT_DATA__\s*=\s*({.*?})\s*</script>",
        r"window\.__PRELOADED_STATE__\s*=\s*({.*?})\s*</script>",
        r"window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>",
        r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>({.*?})</script>',
    ):
        for m in re.finditer(pat, html, re.DOTALL):
            try:
                data = json.loads(m.group(1))
            except json.JSONDecodeError:
                continue
            n = _walk_json_for_shares(data)
            if n:
                return n

    # 3. Generic key:value match anywhere in the HTML (incl. inline JS blobs)
    for m in _SHARES_KEY_RE.finditer(html):
        n = _coerce(m.group(2))
        if n:
            return n

    # 4. Visible text pattern
    for m in _TEXT_RE.finditer(html):
        n = _coerce(m.group(1), m.group(2) or "")
        if n:
            return n

    return None


def _walk_json_for_shares(obj) -> float | None:
    """BFS over nested dict/list looking for shares-outstanding-ish keys."""
    targets = {
        "sharesoutstanding", "totalsharesoutstanding", "numberofshares",
        "fundsharesoutstanding", "sharesouts", "shares_outstanding",
        "shares",
    }
    stack = [obj]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for k, v in node.items():
                kl = str(k).lower().replace("_", "").replace(" ", "")
                if kl in targets:
                    if isinstance(v, (int, float)):
                        n = float(v)
                        if n > 100_000:
                            return n
                    elif isinstance(v, str):
                        n = _coerce(v)
                        if n:
                            return n
                    elif isinstance(v, dict):
                        # nested like {"raw": 12345, "fmt": "12.3M"}
                        for nested_k in ("raw", "r", "value"):
                            if nested_k in v:
                                nv = v[nested_k]
                                if isinstance(nv, (int, float)) and nv > 100_000:
                                    return float(nv)
                                if isinstance(nv, str):
                                    n = _coerce(nv)
                                    if n:
                                        return n
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(node, list):
            stack.extend(node)
    return None
