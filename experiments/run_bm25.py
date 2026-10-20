#!/usr/bin/env python3
"""Run the rank-bm25 lexical baseline on edit2ripple tasks."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from retrieval.bm25 import build_query, evaluate_ranking, rank_files

# Agent Retrieval Bench is a downloaded sibling repository. It supplies only
# benchmark/corpus inputs; implementation and outputs stay in research-project.
DEFAULT_ARB_ROOT = PROJECT_ROOT.parent / "agent-retrieval-bench"
DEFAULT_BENCHMARK = DEFAULT_ARB_ROOT / "data/benchmark/v2_edit2ripple/edit2ripple.jsonl"
DEFAULT_CORPUS = DEFAULT_ARB_ROOT / "data/corpus/v2_edit2ripple"
DEFAULT_OUTPUT = PROJECT_ROOT / "results/bm25_edit2ripple_all.csv"
DEFAULT_SUMMARY = PROJECT_ROOT / "results/bm25_edit2ripple_summary.json"
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
)


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in {path} at line {line_number}: {exc}") from exc


def corpus_path(corpus_dir: Path, sample: dict[str, Any]) -> Path:
    """Match a task to its corpus using repository and base commit.

    The corpus layout replaces '/' in owner/repository with '__'; the commit
    filename then selects the exact repository snapshot for this task.
    """

    repo = str(sample.get("repo") or "")
    base_commit = str(sample.get("base_commit") or "")
    if not repo or not base_commit:
        raise ValueError(f"Task {sample.get('id')!r} is missing repo or base_commit")
    return corpus_dir / repo.replace("/", "__") / f"{base_commit}.chunks.jsonl"


def validate_corpus(chunks: list[dict[str, Any]], sample: dict[str, Any], path: Path) -> None:
    """Fail visibly if a corpus file is not the requested repository snapshot."""

    repo = sample["repo"]
    base_commit = sample["base_commit"]
    mismatch_count = sum(
        chunk.get("repo") != repo or chunk.get("base_commit") != base_commit
        for chunk in chunks
    )
    if mismatch_count:
        raise ValueError(
            f"Corpus {path} contains {mismatch_count} chunks whose repo/base_commit "
            f"does not match {repo}@{base_commit}"
        )


def run(
    benchmark_path: Path,
    corpus_dir: Path,
    output_path: Path,
    limit: int | None = None,
    summary_path: Path | None = None,
) -> dict[str, float | int]:
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive")

    samples: list[dict[str, Any]] = []
    for sample in read_jsonl(benchmark_path):
        samples.append(sample)
        if limit is not None and len(samples) == limit:
            break
    if not samples:
        raise ValueError(f"No benchmark tasks found in {benchmark_path}")

    rows: list[dict[str, Any]] = []
    for sample in samples:
        task_id = str(sample.get("id") or sample.get("task_id") or "")
        query = sample.get("query") or {}
        gold = sample.get("gold") or {}
        anchor_file = str(query.get("anchor_file") or "")
        gold_files = [str(path) for path in gold.get("files") or []]
        if not task_id or not anchor_file or not gold_files:
            raise ValueError(f"Task {task_id!r} is missing id, query.anchor_file, or gold.files")
        if not build_query(sample).strip():
            raise ValueError(f"Task {task_id!r} has an empty intent + anchor_diff query")

        chunks_path = corpus_path(corpus_dir, sample)
        if not chunks_path.is_file():
            raise FileNotFoundError(f"Corpus not found for task {task_id}: {chunks_path}")
        chunks = list(read_jsonl(chunks_path))
        if not chunks:
            raise ValueError(f"Corpus is empty for task {task_id}: {chunks_path}")
        validate_corpus(chunks, sample, chunks_path)

        retrieved = rank_files(sample, chunks, top_k=10)
        top_10_files = [result.path for result in retrieved]
        metrics = evaluate_ranking(gold_files, top_10_files)
        rows.append(
            {
                "task_id": task_id,
                "repo": sample["repo"],
                "base_commit": sample["base_commit"],
                "anchor_file": anchor_file,
                "gold_files": json.dumps(gold_files, ensure_ascii=False),
                "top_10_files": json.dumps(top_10_files, ensure_ascii=False),
                "recall_at_5": metrics.recall_at_5,
                "recall_at_10": metrics.recall_at_10,
                "reciprocal_rank": metrics.reciprocal_rank,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    count = len(rows)
    summary: dict[str, float | int] = {
        "total_tasks_evaluated": count,
        "mean_recall_at_5": sum(float(row["recall_at_5"]) for row in rows) / count,
        "mean_recall_at_10": sum(float(row["recall_at_10"]) for row in rows) / count,
        "mrr": sum(float(row["reciprocal_rank"]) for row in rows) / count,
    }
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
            handle.write("\n")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run(args.benchmark, args.corpus_dir, args.output, args.limit, args.summary)
    print(f"Number of tasks evaluated: {summary['total_tasks_evaluated']}")
    print(f"Mean Recall@5: {summary['mean_recall_at_5']:.4f}")
    print(f"Mean Recall@10: {summary['mean_recall_at_10']:.4f}")
    print(f"MRR: {summary['mrr']:.4f}")
    print(f"Per-task results: {args.output}")
    print(f"Summary: {args.summary}")


if __name__ == "__main__":
    main()
