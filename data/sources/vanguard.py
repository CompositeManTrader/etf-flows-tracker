"""Vanguard: month-end ETF shares outstanding (the only granularity Vanguard publishes).

- fund id comes from the investor-site profile API (which also returns the
  ticker, so the mapping is verified, not hardcoded);
- shares from the advisors-site API `pricing/outstanding-shares` (always the
  latest month end; date parameters are ignored);
- month-end NAV from the investor-site price API's recent NAV history.

These rows feed the separate monthly view only. They must never enter the daily
pipeline: one month-end delta would look like a single-day flow.
"""
from __future__ import annotations

import pandas as pd
from curl_cffi import requests as cffi_requests

TICKERS = ("VOO", "VTI", "VEA", "VGK", "VWO", "BND", "BNDX", "VNQ", "BSV",
           "VGT", "VFH", "VDE", "VHT", "VIS", "VCR", "VDC", "VPU", "VAW", "VOX")

_PROFILE = "https://investor.vanguard.com/vmf/api/{t}/profile"
_PRICE = "https://investor.vanguard.com/vmf/api/{t}/price"
_SHARES = "https://advisors.vanguard.com/investments/products/api/funds/{fid}/pricing/outstanding-shares"


def _json(url: str) -> dict:
    r = cffi_requests.get(url, impersonate="chrome", timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    return r.json()


def _month_end_nav(ticker: str, date: pd.Timestamp) -> float:
    hist = _json(_PRICE.format(t=ticker)).get("historicalPrice", {}).get("nav", [])
    for block in hist:
        for item in block.get("item", []):
            if pd.Timestamp(item["asOfDate"][:10]) == date:
                return float(item["price"])
    return float("nan")


def fetch(ticker: str) -> pd.DataFrame:
    t = ticker.upper()
    profile = _json(_PROFILE.format(t=t))["fundProfile"]
    if profile.get("ticker", "").upper() != t:
        raise ValueError(f"profile returned {profile.get('ticker')} for {t}")
    shares = _json(_SHARES.format(fid=profile["fundId"]))
    date = pd.Timestamp(shares["effectiveDate"]).normalize()
    return pd.DataFrame([{
        "as_of_date": date,
        "shares_outstanding": float(shares["outstandingShares"]),
        "nav": _month_end_nav(t, date),
    }])
