"""Standalone daily snapshot job — fetches shares outstanding and persists to parquet."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.cache import save_daily_snapshot  # noqa: E402
from data.price_loader import check_coverage, fetch_shares_outstanding  # noqa: E402


def main() -> int:
    print("Fetching shares outstanding (yfinance + issuer scrapers)...", flush=True)
    df = fetch_shares_outstanding()
    cov = check_coverage(df)
    print(
        f"Coverage: {cov['covered']}/{cov['total']} ({cov['coverage_pct']:.1f}%)",
        flush=True,
    )

    # Source breakdown
    covered_df = df[df["shares_outstanding"].notna()]
    sources = Counter(covered_df["source"].tolist())
    print("Source breakdown (covered tickers):", flush=True)
    for src, n in sources.most_common():
        print(f"  {src}: {n}", flush=True)

    if cov["missing"]:
        print(f"\nMissing ({len(cov['missing'])}): {', '.join(cov['missing'])}", flush=True)
        miss_sources = Counter(df.loc[df["shares_outstanding"].isna(), "source"].tolist())
        print("Missing-reason breakdown:", flush=True)
        for src, n in miss_sources.most_common():
            print(f"  {src}: {n}", flush=True)

    path = save_daily_snapshot(df)
    print(f"\nSaved snapshot: {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
