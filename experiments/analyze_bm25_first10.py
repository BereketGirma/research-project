#!/usr/bin/env python3
"""Create a compact task-level analysis of the first ten BM25 results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "results/bm25_edit2ripple_first10.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "results/bm25_first10_analysis.csv"

OUTPUT_COLUMNS = (
    "task_id",
    "repo",
    "anchor_file",
    "number_of_gold_files",
    "recall_at_5",
    "recall_at_10",
    "reciprocal_rank",
    "gold_file_ranks",
    "no_gold_in_top_10",
)


def analyze(input_path: Path, output_path: Path) -> None:
    rows: list[dict[str, object]] = []
    with input_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            gold_files = json.loads(row["gold_files"])
            retrieved = json.loads(row["top_10_files"])
            rank_by_path = {path: rank for rank, path in enumerate(retrieved, start=1)}
            gold_ranks = {path: rank_by_path.get(path) for path in gold_files}
            rows.append(
                {
                    "task_id": row["task_id"],
                    "repo": row["repo"],
                    "anchor_file": row["anchor_file"],
                    "number_of_gold_files": len(gold_files),
                    "recall_at_5": row["recall_at_5"],
                    "recall_at_10": row["recall_at_10"],
                    "reciprocal_rank": row["reciprocal_rank"],
                    "gold_file_ranks": json.dumps(gold_ranks, ensure_ascii=False),
                    "no_gold_in_top_10": not any(rank is not None for rank in gold_ranks.values()),
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    analyze(args.input, args.output)
    print(f"Analysis: {args.output}")
