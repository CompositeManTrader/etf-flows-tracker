"""ProShares: official historical NAV CSV (daily NAV + Shares Outstanding in thousands)."""
from __future__ import annotations

import io

import pandas as pd

from ._http import get

_URL = "https://accounts.profunds.com/etfdata/ByFund/{T}-historical_nav.csv"


def fetch(ticker: str) -> pd.DataFrame:
    raw = pd.read_csv(io.StringIO(get(_URL.format(T=ticker.upper())).text))
    df = pd.DataFrame({
        "as_of_date": pd.to_datetime(raw["Date"], format="%m/%d/%Y", errors="coerce"),
        "nav": pd.to_numeric(raw["NAV"], errors="coerce"),
        "shares_outstanding": pd.to_numeric(raw["Shares Outstanding (000)"], errors="coerce") * 1000,
    })
    return df.dropna(subset=["as_of_date"])
