"""iShares (BlackRock) scraper.

Strategy: per-ETF AJAX endpoint that returns CSV fund stats. Needs the
product_id per ticker (hardcoded mapping). The CSV contains rows with
labels like "Shares Outstanding" and the numeric value.

Falls back to scraping the per-ETF product page HTML if the AJAX endpoint
returns nothing usable.
"""
from __future__ import annotations

import re

from ._http import get_text
from ._parse import find_shares_in_html

# ticker -> (product_id, slug)
# Slug is optional; iShares accepts product_id + any slug (it redirects).
_PRODUCT_IDS: dict[str, tuple[int, str]] = {
    "IVV":  (239726, "ishares-core-sp-500-etf"),
    "IWM":  (239710, "ishares-russell-2000-etf"),
    "MTUM": (251614, "ishares-msci-usa-momentum-factor-etf"),
    "QUAL": (256101, "ishares-msci-usa-quality-factor-etf"),
    "USMV": (239693, "ishares-msci-usa-min-vol-factor-etf"),
    "VLUE": (251616, "ishares-msci-usa-value-factor-etf"),
    "SIZE": (251615, "ishares-msci-usa-size-factor-etf"),
    "IWF":  (239706, "ishares-russell-1000-growth-etf"),
    "IWD":  (239708, "ishares-russell-1000-value-etf"),
    "IWN":  (239709, "ishares-russell-2000-value-etf"),
    "IWO":  (239711, "ishares-russell-2000-growth-etf"),
    "SOXX": (239705, "ishares-semiconductor-etf"),
    "ICLN": (239738, "ishares-global-clean-energy-etf"),
    "IBB":  (239699, "ishares-biotechnology-etf"),
    "EFA":  (239623, "ishares-msci-eafe-etf"),
    "IEFA": (244049, "ishares-core-msci-eafe-etf"),
    "EWJ":  (239665, "ishares-msci-japan-etf"),
    "EWU":  (239690, "ishares-msci-united-kingdom-etf"),
    "EWG":  (239658, "ishares-msci-germany-etf"),
    "EWQ":  (239656, "ishares-msci-france-etf"),
    "EEM":  (239637, "ishares-msci-emerging-markets-etf"),
    "IEMG": (244050, "ishares-core-msci-emerging-markets-etf"),
    "FXI":  (239536, "ishares-china-largecap-etf"),
    "MCHI": (239619, "ishares-msci-china-etf"),
    "EWZ":  (239612, "ishares-msci-brazil-etf"),
    "EWW":  (239681, "ishares-msci-mexico-etf"),
    "INDA": (244052, "ishares-msci-india-etf"),
    "AGG":  (239458, "ishares-core-total-us-bond-market-etf"),
    "TLT":  (239454, "ishares-20-year-treasury-bond-etf"),
    "IEF":  (239456, "ishares-7-10-year-treasury-bond-etf"),
    "SHY":  (239452, "ishares-1-3-year-treasury-bond-etf"),
    "LQD":  (239566, "ishares-iboxx-investment-grade-corporate-bond-etf"),
    "HYG":  (239565, "ishares-iboxx-high-yield-corporate-bond-etf"),
    "TIP":  (239467, "ishares-tips-bond-etf"),
    "MBB":  (239465, "ishares-mbs-etf"),
    "EMB":  (239572, "ishares-jp-morgan-usd-emerging-markets-bond-etf"),
    "IGOV": (239493, "ishares-international-treasury-bond-etf"),
    "IAU":  (239561, "ishares-gold-trust-fund"),
    "SLV":  (239855, "ishares-silver-trust-fund"),
    "IYR":  (239520, "ishares-us-real-estate-etf"),
    "REM":  (239512, "ishares-mortgage-real-estate-etf"),
    "IBIT": (333011, "ishares-bitcoin-trust"),
    "ETHA": (333890, "ishares-ethereum-trust-etf"),
    "HEFA": (272335, "ishares-currency-hedged-msci-eafe-etf"),
    "SHV":  (239466, "ishares-short-treasury-bond-etf"),
}


def _ajax_csv_url(product_id: int, ticker: str) -> str:
    return (
        f"https://www.ishares.com/us/products/{product_id}/fund/1467271812596.ajax"
        f"?fileType=csv&fileName={ticker}_fund&dataType=fund"
    )


def _product_page_url(product_id: int, slug: str) -> str:
    return f"https://www.ishares.com/us/products/{product_id}/{slug}"


_SHARES_LABEL_RE = re.compile(
    r"shares?\s*outstanding|total\s+shares|number\s+of\s+shares",
    re.IGNORECASE,
)


def _parse_csv(text: str) -> float | None:
    """iShares fund CSV: 'label,"value"' rows. Find shares-outstanding row."""
    if not text:
        return None
    for raw_line in text.splitlines():
        if not _SHARES_LABEL_RE.search(raw_line):
            continue
        # split on comma, take last cell with a number
        parts = [p.strip().strip('"') for p in raw_line.split(",")]
        for p in reversed(parts):
            n = _to_number(p)
            if n and n > 100_000:  # sanity floor (ETFs always >100k shares)
                return n
    return None


def _parse_html(html: str) -> float | None:
    if not html:
        return None
    # Multiple patterns the page might use
    patterns = [
        r"Shares\s+Outstanding[^0-9\-]{1,120}([\d,\.]+)\s*(M|Million|B|Billion)?",
        r'"sharesOutstanding"\s*:\s*"?([\d,\.]+)"?',
        r"Total\s+Shares\s+Outstanding[^0-9\-]{1,120}([\d,\.]+)\s*(M|Million|B|Billion)?",
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if not m:
            continue
        n = _to_number(m.group(1))
        if n is None:
            continue
        suffix = ""
        if m.lastindex and m.lastindex >= 2 and m.group(2):
            suffix = m.group(2).upper()
        if suffix.startswith("M"):
            n *= 1_000_000
        elif suffix.startswith("B"):
            n *= 1_000_000_000
        if n > 100_000:
            return n
    return None


def _to_number(v) -> float | None:
    if v is None:
        return None
    try:
        cleaned = str(v).replace(",", "").replace("$", "").strip()
        if not cleaned or cleaned in ("-", "--", "N/A"):
            return None
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def fetch(ticker: str) -> float | None:
    info = _PRODUCT_IDS.get(ticker.upper())
    if not info:
        return None
    product_id, slug = info

    csv_text = get_text(
        _ajax_csv_url(product_id, ticker.upper()),
        headers={"Referer": _product_page_url(product_id, slug)},
    )
    shares = _parse_csv(csv_text or "")
    if shares:
        return shares

    html = get_text(_product_page_url(product_id, slug))
    if html:
        shares = _parse_html(html) or find_shares_in_html(html)
        if shares:
            return shares
    return None
