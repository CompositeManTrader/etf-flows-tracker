"""Invesco: the price-listing API behind invesco.com product pages (shares + NAV, current value only).

The payload's `effectiveDate` is the publication date: its NAV and closingPrice
belong to the PREVIOUS session (verified Oct 2026: QQQ closingPrice 749.58 =
Oct 2 close while effectiveDate was Oct 5). Rows are therefore stored under the
prior trading day.

The payload carries no ticker, so each CUSIP below was matched to its ticker by
comparing closingPrice with the market close.
"""
from __future__ import annotations

import json

import pandas as pd
from curl_cffi import requests as cffi_requests

from core.trading_calendar import previous_trading_day

CUSIPS: dict[str, str] = {
    "QQQ": "46090E103",
    "QQQM": "46138G649",
    "DBA": "46140H106",
    "DBC": "46138B103",
    "PDBC": "46090F100",
}

_URL = ("https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/{c}/prices"
        "?idType=cusip&variationType=priceListing&productType=ETF&productSubType=ETF")


def fetch(ticker: str) -> pd.DataFrame:
    # Invesco's bot filter answers 406 when a Chrome User-Agent arrives with a
    # non-Chrome TLS fingerprint (plain `requests`); curl_cffi makes both match.
    resp = cffi_requests.get(_URL.format(c=CUSIPS[ticker.upper()]), impersonate="chrome", timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")
    payload = json.loads(resp.text)
    if not isinstance(payload, dict) or "sharesOutstanding" not in payload:
        raise ValueError(f"empty payload for CUSIP {CUSIPS[ticker.upper()]}")
    return pd.DataFrame([{
        "as_of_date": previous_trading_day(pd.Timestamp(payload["effectiveDate"])),
        "shares_outstanding": float(payload["sharesOutstanding"]),
        "nav": float(payload["nav"]) if payload.get("nav") is not None else float("nan"),
    }])
