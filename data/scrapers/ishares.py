"""iShares (BlackRock) scraper.

Strategy: hit the product-screener JSON endpoint ONCE per scraper-session and
cache the full table of all iShares US ETFs. Then look up by ticker.

The endpoint returns a JSON-like blob wrapped in JS callback or with leading
characters. We strip those and parse.

Reference field name in iShares JSON: `totalNetAssets` (USD AUM),
`sharesOutstanding` (number of shares).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from ._http import get_text

_SCREENER_URLS = (
    # all US iShares + BlackRock equity/fi
    "https://www.ishares.com/us/product-screener/product-screener-v3.1.jsn"
    "?dcrPath=/templatedata/config/product-screener-v3/data/en/us-ishares/all"
    "&siteEntryPassthrough=true",
)


def _strip_jsonp(text: str) -> str:
    """iShares wraps JSON sometimes in callback(...), sometimes with leading garbage."""
    text = text.strip()
    # Strip JSONP wrapping like `callbackName({...})`
    m = re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*\((.*)\)\s*;?\s*$", text, re.DOTALL)
    if m:
        return m.group(1)
    return text


def _to_number(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict):
        # iShares often nests: {"r": 12345.67, "d": "12.3M"}
        for key in ("r", "raw", "value"):
            if key in v:
                return _to_number(v[key])
    if isinstance(v, str):
        cleaned = v.replace(",", "").replace("$", "").strip()
        if not cleaned or cleaned in ("-", "--", "N/A"):
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


@lru_cache(maxsize=1)
def _load_screener() -> dict[str, dict]:
    """Returns {ticker_upper: row_dict} for all iShares ETFs in the screener."""
    out: dict[str, dict] = {}
    for url in _SCREENER_URLS:
        text = get_text(url, headers={"Referer": "https://www.ishares.com/us/products/etf-investments"})
        if not text:
            continue
        payload = _strip_jsonp(text)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        # Data shape: {someKey: {...rows keyed by productId...}} OR {"data": {...}}
        rows = []
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, dict):
                    for row in v.values():
                        if isinstance(row, dict):
                            rows.append(row)
        elif isinstance(data, list):
            rows = [r for r in data if isinstance(r, dict)]

        for row in rows:
            ticker = row.get("localExchangeTicker") or row.get("ticker") or row.get("symbol")
            if isinstance(ticker, str):
                out[ticker.upper()] = row
        if out:
            break
    return out


def fetch(ticker: str) -> float | None:
    table = _load_screener()
    row = table.get(ticker.upper())
    if not row:
        return None
    # Try a series of likely field names
    for key in ("sharesOutstanding", "totalSharesOutstanding", "numberOfShares", "shares"):
        if key in row:
            val = _to_number(row[key])
            if val and val > 0:
                return val
    return None
