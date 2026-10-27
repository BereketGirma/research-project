#!/usr/bin/env python3
"""Fuse saved BM25 and semantic file rankings with RRF."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from retrieval.bm25 import evaluate_ranking
from retrieval.hybrid import DEFAULT_RRF_K, reciprocal_rank_fusion

DEFAULT_BM25 = PROJECT_ROOT / "results/bm25_edit2ripple_all.csv"
DEFAULT_SEMANTIC = PROJECT_ROOT / "results/semantic_edit2ripple_all.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "results/hybrid_edit2ripple_all.csv"
DEFAULT_SUMMARY = PROJECT_ROOT / "results/hybrid_edit2ripple_summary.json"
CSV_COLUMNS = (
    "task_id",
    "repo",
    "base_commit",
    "anchor_file",
    "gold_files",
    "top_10_files",
    "recall_at_5",
    "recall_at_10",
    "reciprocal_rank",
    "rrf_k",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run(
    bm25_path: Path,
    semantic_path: Path,
    output_path: Path,
    *,
    limit: int | None = None,
    rrf_k: int = DEFAULT_RRF_K,
    summary_path: Path | None = None,
) -> dict[str, float | int | str]:
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive")
    started_at = time.perf_counter()
    bm25_rows = read_csv(bm25_path)
    semantic_rows = read_csv(semantic_path)
    if limit is not None:
        bm25_rows = bm25_rows[:limit]
        semantic_rows = semantic_rows[:limit]
    if not bm25_rows or len(bm25_rows) != len(semantic_rows):
        raise ValueError("BM25 and semantic inputs must contain the same non-zero number of tasks")

    rows: list[dict[str, Any]] = []
    for bm25, semantic in zip(bm25_rows, semantic_rows):
        for field in ("task_id", "repo", "base_commit", "anchor_file", "gold_files"):
            if bm25[field] != semantic[field]:
                raise ValueError(f"Input mismatch for field {field}: {bm25.get('task_id')}")
        gold_files = json.loads(bm25["gold_files"])
        bm25_files = json.loads(bm25["top_10_files"])
        semantic_files = json.loads(semantic["top_10_files"])
        results = reciprocal_rank_fusion(
            bm25_files,
            semantic_files,
            anchor_file=bm25["anchor_file"],
            top_k=10,
            rrf_k=rrf_k,
        )
        top_10_files = [result.path for result in results]
        metrics = evaluate_ranking(gold_files, top_10_files)
        rows.append(
            {
                "task_id": bm25["task_id"],
                "repo": bm25["repo"],
                "base_commit": bm25["base_commit"],
                "anchor_file": bm25["anchor_file"],
                "gold_files": bm25["gold_files"],
                "top_10_files": json.dumps(top_10_files, ensure_ascii=False),
                "recall_at_5": metrics.recall_at_5,
                "recall_at_10": metrics.recall_at_10,
                "reciprocal_rank": metrics.reciprocal_rank,
                "rrf_k": rrf_k,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    count = len(rows)
    summary: dict[str, float | int | str] = {
        "total_tasks_evaluated": count,
        "mean_recall_at_5": sum(float(row["recall_at_5"]) for row in rows) / count,
        "mean_recall_at_10": sum(float(row["recall_at_10"]) for row in rows) / count,
        "mrr": sum(float(row["reciprocal_rank"]) for row in rows) / count,
        "fusion": "reciprocal_rank_fusion",
        "rrf_k": rrf_k,
        "elapsed_seconds": time.perf_counter() - started_at,
    }
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
            handle.write("\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bm25", type=Path, default=DEFAULT_BM25)
    parser.add_argument("--semantic", type=Path, default=DEFAULT_SEMANTIC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--rrf-k", type=int, default=DEFAULT_RRF_K)
    args = parser.parse_args()
    summary = run(
        args.bm25,
        args.semantic,
        args.output,
        limit=args.limit,
        rrf_k=args.rrf_k,
        summary_path=args.summary,
    )
    print(f"Number of tasks evaluated: {summary['total_tasks_evaluated']}")
    print(f"Mean Recall@5: {summary['mean_recall_at_5']:.4f}")
    print(f"Mean Recall@10: {summary['mean_recall_at_10']:.4f}")
    print(f"MRR: {summary['mrr']:.4f}")
    print(f"RRF k: {summary['rrf_k']}")
    print(f"Per-task results: {args.output}")
    print(f"Summary: {args.summary}")


if __name__ == "__main__":
    main()
