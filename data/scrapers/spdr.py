"""SPDR (State Street) scraper.

Strategy: SPDR exposes per-ETF XLSX files at:
  https://www.ssga.com/library-content/products/fund-data/etfs/us/{filename}-us-en-{ticker_lower}.xlsx

We try the 'holdings-daily' file first (most reliable, daily refresh) which
includes a fund-level metadata section near the top with "Shares Outstanding".

Falls back to the HTML product page parse if the XLSX isn't available.
"""
from __future__ import annotations

import io
import re

from ._http import get_bytes, get_text

_XLSX_URL = (
    "https://www.ssga.com/library-content/products/fund-data/etfs/us/"
    "holdings-daily-us-en-{ticker}.xlsx"
)
_PRODUCT_PAGE_URLS = (
    "https://www.ssga.com/us/en/intermediary/etfs/{slug}",
    "https://www.ssga.com/us/en/individual/etfs/{slug}",
)

# Optional slugs for fund pages (used only by HTML fallback)
_SLUGS = {
    "SPY": "spdr-sp-500-etf-trust-spy",
    "DIA": "spdr-dow-jones-industrial-average-etf-trust-dia",
    "XLK": "the-technology-select-sector-spdr-fund-xlk",
    "XLF": "the-financial-select-sector-spdr-fund-xlf",
    "XLE": "the-energy-select-sector-spdr-fund-xle",
    "XLV": "the-health-care-select-sector-spdr-fund-xlv",
    "XLI": "the-industrial-select-sector-spdr-fund-xli",
    "XLY": "the-consumer-discretionary-select-sector-spdr-fund-xly",
    "XLP": "the-consumer-staples-select-sector-spdr-fund-xlp",
    "XLU": "the-utilities-select-sector-spdr-fund-xlu",
    "XLB": "the-materials-select-sector-spdr-fund-xlb",
    "XLRE": "the-real-estate-select-sector-spdr-fund-xlre",
    "XLC": "the-communication-services-select-sector-spdr-fund-xlc",
    "GLD": "spdr-gold-shares-gld",
    "JNK": "spdr-bloomberg-high-yield-bond-etf-jnk",
    "XBI": "spdr-sp-biotech-etf-xbi",
    "BIL": "spdr-bloomberg-1-3-month-t-bill-etf-bil",
}


def _parse_xlsx_for_shares(blob: bytes) -> float | None:
    try:
        import openpyxl  # noqa: WPS433
    except ImportError:
        return None
    try:
        wb = openpyxl.load_workbook(io.BytesIO(blob), data_only=True, read_only=True)
    except Exception:  # noqa: BLE001
        return None
    for ws in wb.worksheets:
        # SPDR holdings files have a small metadata block in the top rows
        # with label/value cell pairs. We scan the first ~40 rows.
        for row in ws.iter_rows(min_row=1, max_row=40, values_only=True):
            if not row:
                continue
            for i, cell in enumerate(row):
                if cell is None:
                    continue
                label = str(cell).strip().lower()
                if "shares outstanding" in label or "shares oustanding" in label:
                    # value usually in next cell or two cells over
                    for j in (i + 1, i + 2, i + 3):
                        if j < len(row) and row[j] is not None:
                            val = _coerce_number(row[j])
                            if val and val > 0:
                                return val
    return None


def _parse_html_for_shares(html: str) -> float | None:
    # Look for "Shares Outstanding ... 1,038.03 M" or similar patterns
    patterns = [
        r"Shares\s+Outstanding[^0-9]{1,40}([\d,\.]+)\s*(M|Million|B|Billion)?",
        r"Number\s+of\s+Shares[^0-9]{1,40}([\d,\.]+)\s*(M|Million|B|Billion)?",
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if not m:
            continue
        num = _coerce_number(m.group(1))
        if num is None:
            continue
        suffix = (m.group(2) or "").upper()
        if suffix.startswith("M"):
            num *= 1_000_000
        elif suffix.startswith("B"):
            num *= 1_000_000_000
        if num > 0:
            return num
    return None


def _coerce_number(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except (ValueError, AttributeError):
        return None


def fetch(ticker: str) -> float | None:
    blob = get_bytes(_XLSX_URL.format(ticker=ticker.lower()))
    if blob:
        shares = _parse_xlsx_for_shares(blob)
        if shares:
            return shares

    slug = _SLUGS.get(ticker.upper())
    if slug:
        for url_tmpl in _PRODUCT_PAGE_URLS:
            html = get_text(url_tmpl.format(slug=slug))
            if html:
                shares = _parse_html_for_shares(html)
                if shares:
                    return shares
    return None
