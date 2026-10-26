"""Command-line entry point: python -m lead_deduper leads.csv -o clean.csv"""
from __future__ import annotations

import argparse
import csv
import sys
from typing import List, Optional

from .dedupe import FIELDS, dedupe

EXTRA_FIELDS = ["merged_ids", "match_reasons", "score", "score_notes"]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lead_deduper", description="Merge duplicate leads from one or more CSV files and score them."
    )
    parser.add_argument("csv", nargs="+", help="one or more lead CSVs (columns: " + ", ".join(FIELDS) + ")")
    parser.add_argument("-o", "--output", help="write the clean list here (default: print a summary only)")
    parser.add_argument("--threshold", type=float, default=0.85,
                        help="name similarity needed for a fuzzy match, 0-1 (default 0.85)")
    args = parser.parse_args(argv)

    leads = []
    for path in args.csv:
        try:
            with open(path, newline="", encoding="utf-8") as f:
                leads.extend(csv.DictReader(f))
        except OSError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    results = sorted(dedupe(leads, args.threshold), key=lambda r: r.score, reverse=True)
    merged = [r for r in results if len(r.source_ids) > 1]

    print(f"{len(leads)} rows in -> {len(results)} unique leads "
          f"({len(leads) - len(results)} duplicates merged into {len(merged)} records)")
    if merged:
        print("\nMerged:")
        for r in merged:
            print(f"  {r.record.get('name', '?'):<22} ids {', '.join(r.source_ids):<16} {'; '.join(r.reasons)}")

    print("\nTop leads:")
    for r in results[:5]:
        print(f"  {r.score:>3}  {r.record.get('name', ''):<22} {r.record.get('company', ''):<26} {', '.join(r.score_notes)}")

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS + EXTRA_FIELDS, extrasaction="ignore")
            writer.writeheader()
            for r in results:
                writer.writerow({
                    **r.record,
                    "merged_ids": "; ".join(r.source_ids),
                    "match_reasons": "; ".join(r.reasons),
                    "score": r.score,
                    "score_notes": ", ".join(r.score_notes),
                })
        print(f"\nWrote {len(results)} leads to {args.output}")
    return 0
