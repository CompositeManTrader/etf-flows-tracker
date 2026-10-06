"""Single-fund product pages that print shares outstanding as plain text.

When the page shows no as-of date, the value is labelled with the last
completed NYSE session and flagged `as_of_inferred` (the job's morning run
re-fetches and overwrites that session once the page has updated).
"""
from __future__ import annotations

import re

import pandas as pd

from core.trading_calendar import last_completed_session

from ._http import get, html_to_text, to_float

# ticker -> (url, shares regex, as-of regex or None, nav regex or None)
PAGES: dict[str, tuple[str, str, str | None, str | None]] = {
    "KWEB": ("https://kraneshares.com/kweb/",
             r"Shares Outstanding\s*([\d,]+)",
             r"NAV as of (\d{2}/\d{2}/\d{4})",
             r"NAV as of \d{2}/\d{2}/\d{4}\s*\$([\d,\.]+)"),
    "SVOL": ("https://www.simplify.us/etfs/svol-simplify-volatility-premium-etf",
             r"Shares Outstanding\s*([\d,]+)",
             None, None),
    "BITB": ("https://bitbetf.com/",
             r"Shares Outstanding\s*([\d,]+)",
             None, None),
}


def fetch(ticker: str) -> pd.DataFrame:
    url, sh_re, date_re, nav_re = PAGES[ticker.upper()]
    text = html_to_text(get(url).text)

    m = re.search(sh_re, text, re.I)
    if not m:
        raise ValueError("shares value not found")

    inferred = True
    as_of = last_completed_session()
    if date_re and (d := re.search(date_re, text, re.I)):
        as_of, inferred = pd.to_datetime(d.group(1), format="%m/%d/%Y"), False

    nav = float("nan")
    if nav_re and not inferred and (n := re.search(nav_re, text, re.I)):
        nav = to_float(n.group(1))

    return pd.DataFrame([{
        "as_of_date": as_of, "shares_outstanding": to_float(m.group(1)),
        "nav": nav, "as_of_inferred": inferred,
    }])
