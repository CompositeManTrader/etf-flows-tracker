"""State Street SPDR: official daily NAV history XLSX (Date, NAV, Shares Outstanding, TNA).

One file per fund, with full daily history, so a single fetch also backfills.
"""
from __future__ import annotations

import io

import pandas as pd

from ._http import get

_URL = "https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-{t}.xlsx"


def fetch(ticker: str) -> pd.DataFrame:
    import openpyxl

    blob = get(_URL.format(t=ticker.lower())).content
    ws = openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=True).worksheets[0]

    rows, header_seen = [], False
    for row in ws.iter_rows(values_only=True):
        if not header_seen:
            header_seen = row[0] == "Date" and "Shares Outstanding" in row
            if header_seen:
                cols = list(row)
                i_date, i_nav, i_sh = cols.index("Date"), cols.index("NAV"), cols.index("Shares Outstanding")
            continue
        if row[i_date] is None:
            break
        rows.append((row[i_date], row[i_nav], row[i_sh]))

    if not header_seen:
        raise ValueError("header 'Date | NAV | Shares Outstanding' not found")

    df = pd.DataFrame(rows, columns=["as_of_date", "nav", "shares_outstanding"])
    df["as_of_date"] = pd.to_datetime(df["as_of_date"], format="%d-%b-%Y", errors="coerce")
    return df.dropna(subset=["as_of_date"])
