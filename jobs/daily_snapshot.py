"""Standalone daily snapshot job — fetches shares outstanding and persists to parquet."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.cache import save_daily_snapshot  # noqa: E402
from data.price_loader import check_coverage, fetch_shares_outstanding  # noqa: E402


def main() -> int:
    print("Fetching shares outstanding from yfinance...", flush=True)
    df = fetch_shares_outstanding()
    cov = check_coverage(df)
    print(
        f"Coverage: {cov['covered']}/{cov['total']} ({cov['coverage_pct']:.1f}%)",
        flush=True,
    )
    if cov["missing"]:
        print(f"Missing ({len(cov['missing'])}): {', '.join(cov['missing'])}", flush=True)

    path = save_daily_snapshot(df)
    print(f"Saved snapshot: {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
