"""iShares: product page key-facts block "Shares Outstanding <n> as of <date>" + NAV from JSON-LD.

Only the current value is published, so history accumulates one row per session.
The page title must contain the ticker, so a wrong product id can't silently
return another fund's numbers.
"""
from __future__ import annotations

import re

import pandas as pd

from ._http import get, html_to_text, to_float

# ticker -> (product_id, slug); iShares redirects any slug, the id is what matters
PRODUCTS: dict[str, tuple[int, str]] = {
    "IVV":  (239726, "ishares-core-sp-500-etf"),
    "IWM":  (239710, "ishares-russell-2000-etf"),
    "MTUM": (251614, "ishares-msci-usa-momentum-factor-etf"),
    "QUAL": (256101, "ishares-msci-usa-quality-factor-etf"),
    "USMV": (239695, "ishares-msci-usa-min-vol-factor-etf"),
    "VLUE": (251616, "ishares-msci-usa-value-factor-etf"),
    "SIZE": (251465, "ishares-msci-usa-size-factor-etf"),
    "IWF":  (239706, "ishares-russell-1000-growth-etf"),
    "IWD":  (239708, "ishares-russell-1000-value-etf"),
    "IWN":  (239712, "ishares-russell-2000-value-etf"),
    "IWO":  (239709, "ishares-russell-2000-growth-etf"),
    "SOXX": (239705, "ishares-semiconductor-etf"),
    "ICLN": (239738, "ishares-global-clean-energy-etf"),
    "IBB":  (239699, "ishares-biotechnology-etf"),
    "EFA":  (239623, "ishares-msci-eafe-etf"),
    "IEFA": (244049, "ishares-core-msci-eafe-etf"),
    "EWJ":  (239665, "ishares-msci-japan-etf"),
    "EWU":  (239690, "ishares-msci-united-kingdom-etf"),
    "EWG":  (239650, "ishares-msci-germany-etf"),
    "EWQ":  (239648, "ishares-msci-france-etf"),
    "EEM":  (239637, "ishares-msci-emerging-markets-etf"),
    "IEMG": (244050, "ishares-core-msci-emerging-markets-etf"),
    "FXI":  (239536, "ishares-china-largecap-etf"),
    "MCHI": (239619, "ishares-msci-china-etf"),
    "EWZ":  (239612, "ishares-msci-brazil-etf"),
    "EWW":  (239670, "ishares-msci-mexico-capped-etf"),
    "INDA": (239659, "ishares-msci-india-etf"),
    "AGG":  (239458, "ishares-core-total-us-bond-market-etf"),
    "TLT":  (239454, "ishares-20-year-treasury-bond-etf"),
    "IEF":  (239456, "ishares-7-10-year-treasury-bond-etf"),
    "SHY":  (239452, "ishares-1-3-year-treasury-bond-etf"),
    "LQD":  (239566, "ishares-iboxx-investment-grade-corporate-bond-etf"),
    "HYG":  (239565, "ishares-iboxx-high-yield-corporate-bond-etf"),
    "TIP":  (239467, "ishares-tips-bond-etf"),
    "MBB":  (239465, "ishares-mbs-etf"),
    "EMB":  (239572, "ishares-jp-morgan-usd-emerging-markets-bond-etf"),
    "IGOV": (239830, "ishares-international-treasury-bond-etf"),
    "IAU":  (239561, "ishares-gold-trust-fund"),
    "SLV":  (239855, "ishares-silver-trust-fund"),
    "IYR":  (239520, "ishares-us-real-estate-etf"),
    "REM":  (239543, "ishares-mortgage-real-estate-etf"),
    "IBIT": (333011, "ishares-bitcoin-trust"),
    "ETHA": (337614, "ishares-ethereum-trust-etf"),
    "HEFA": (259622, "ishares-currency-hedged-msci-eafe-etf"),
    "SHV":  (239466, "ishares-short-treasury-bond-etf"),
    # US sector ETFs
    "IYW":  (239522, "ishares-u-s-technology-etf"),
    "IYF":  (239508, "ishares-u-s-financials-etf"),
    "IYE":  (239507, "ishares-u-s-energy-etf"),
    "IYH":  (239511, "ishares-u-s-healthcare-etf"),
    "IYJ":  (239514, "ishares-u-s-industrials-etf"),
    "IYC":  (239506, "ishares-u-s-consumer-discretionary-etf"),
    "IYK":  (239505, "ishares-u-s-consumer-staples-etf"),
    "IDU":  (239524, "ishares-u-s-utilities-etf"),
    "IYM":  (239503, "ishares-u-s-basic-materials-etf"),
    "IYZ":  (239523, "ishares-u-s-telecommunications-etf"),
}

_URL = "https://www.ishares.com/us/products/{pid}/{slug}"
_SHARES_RE = re.compile(r"([\d,]+(?:\.\d+)?)\s*as of\s*([A-Z][a-z]{2} \d{1,2}, \d{4})")
_NAV_RE = re.compile(r'"name":"NAV as of","value":"([\d,\.]+)"')
_NAV_DATE_RE = re.compile(r'"name":"As of Dates","value":"([A-Z][a-z]{2} \d{1,2}, \d{4})"')


def fetch(ticker: str) -> pd.DataFrame:
    t = ticker.upper()
    pid, slug = PRODUCTS[t]
    html = get(_URL.format(pid=pid, slug=slug)).text

    title = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    if not title or not re.search(rf"\b{t}\b", title.group(1)):
        raise ValueError(f"product {pid} page is not {t} (title: {title.group(1).strip()[:60] if title else '?'})")

    i = html.find('keyFundFacts-sharesOutstanding-data')
    if i < 0:
        raise ValueError("sharesOutstanding block not found")
    m = _SHARES_RE.search(html_to_text(html[i: i + 1500]))
    if not m:
        raise ValueError("sharesOutstanding value not parsed")
    as_of = pd.to_datetime(m.group(2), format="%b %d, %Y")

    nav = float("nan")
    nm, dm = _NAV_RE.search(html), _NAV_DATE_RE.search(html)
    if nm and dm and pd.to_datetime(dm.group(1), format="%b %d, %Y") == as_of:
        nav = to_float(nm.group(1))

    return pd.DataFrame([{"as_of_date": as_of, "shares_outstanding": to_float(m.group(1)), "nav": nav}])
