"""Fetch official shares outstanding for every ticker and upsert by (ticker, as_of_date).

Safe to run any number of times per day: each issuer number is stored under the
trading session it belongs to, so late or repeated runs can't mislabel days.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from data.cache import save_status, upsert_history, upsert_monthly  # noqa: E402
from data.shares_loader import fetch_all  # noqa: E402
from data.sources import vanguard  # noqa: E402


def snapshot_vanguard_monthly() -> None:
    """Month-end Vanguard shares, stored apart from the daily history."""
    rows = []
    run_at = pd.Timestamp.now(tz="UTC").tz_localize(None)
    for t in vanguard.TICKERS:
        try:
            rows.append(vanguard.fetch(t).assign(ticker=t, fetched_at=run_at))
        except Exception as e:  # noqa: BLE001
            print(f"  ! Vanguard {t}: {type(e).__name__}: {str(e)[:120]}", flush=True)
    if rows:
        m = upsert_monthly(pd.concat(rows, ignore_index=True))
        print(f"Vanguard monthly: {len(rows)}/{len(vanguard.TICKERS)} fetched; "
              f"{len(m)} rows, month ends {sorted(m['as_of_date'].dt.date.unique())}", flush=True)


def main() -> int:
    print("Fetching official shares outstanding...", flush=True)
    obs, status = fetch_all()

    n = len(status)
    ok = status[status["status"] == "ok"]
    print(f"Coverage: {len(ok)}/{n} ({len(ok) / n:.1%})", flush=True)
    print(status.groupby(["source", "status"], dropna=False).size().to_string(), flush=True)

    bad = status[status["status"].isin(["error", "rejected"])]
    for _, r in bad.iterrows():
        print(f"  ! {r.ticker} [{r.source}] {r.status}: {r.detail}", flush=True)
    print("No reliable source:", ", ".join(status.loc[status["status"] == "no_source", "ticker"]), flush=True)

    save_status(status)
    try:  # the monthly Vanguard view must never block the daily snapshot
        snapshot_vanguard_monthly()
    except Exception as e:  # noqa: BLE001
        print(f"  ! Vanguard monthly failed: {type(e).__name__}: {e}", flush=True)
    if obs.empty:
        print("No observations fetched; history left untouched.", flush=True)
        return 1

    hist = upsert_history(obs)
    print(f"History: {len(hist)} rows, {hist['ticker'].nunique()} tickers, "
          f"{hist['as_of_date'].min().date()}..{hist['as_of_date'].max().date()}", flush=True)
    print("Latest as-of by source:", ok.groupby("source")["last_as_of"].max().dt.date.to_dict(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
