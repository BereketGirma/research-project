#!/usr/bin/env python3
"""Run the sentence-transformer semantic baseline on edit2ripple tasks."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from experiments.run_bm25 import corpus_path, read_jsonl, validate_corpus
from retrieval.bm25 import build_query, evaluate_ranking
from retrieval.semantic import DEFAULT_MODEL_NAME, encode_chunks, load_model, rank_files

DEFAULT_ARB_ROOT = PROJECT_ROOT.parent / "agent-retrieval-bench"
DEFAULT_BENCHMARK = DEFAULT_ARB_ROOT / "data/benchmark/v2_edit2ripple/edit2ripple.jsonl"
DEFAULT_CORPUS = DEFAULT_ARB_ROOT / "data/corpus/v2_edit2ripple"
DEFAULT_OUTPUT = PROJECT_ROOT / "results/semantic_edit2ripple_first10.csv"
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
    "model",
)


def run(
    benchmark_path: Path,
    corpus_dir: Path,
    output_path: Path,
    limit: int = 10,
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = 64,
) -> dict[str, float | int | str]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    samples = []
    for sample in read_jsonl(benchmark_path):
        samples.append(sample)
        if len(samples) == limit:
            break
    if not samples:
        raise ValueError(f"No benchmark tasks found in {benchmark_path}")

    model = load_model(model_name, device="cpu")
    # Keyed by the exact snapshot path. Reuse changes runtime only: each chunk
    # is independently encoded and task-specific anchor exclusion happens later.
    snapshot_cache: dict[Path, tuple[list[dict[str, Any]], Any]] = {}
    rows: list[dict[str, Any]] = []
    for task_number, sample in enumerate(samples, start=1):
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
        if chunks_path not in snapshot_cache:
            chunks = list(read_jsonl(chunks_path))
            if not chunks:
                raise ValueError(f"Corpus is empty for task {task_id}: {chunks_path}")
            validate_corpus(chunks, sample, chunks_path)
            print(f"Encoding snapshot for task {task_number}/{len(samples)}: {chunks_path.name}", flush=True)
            snapshot_cache[chunks_path] = (chunks, encode_chunks(chunks, model, batch_size=batch_size))
        chunks, embeddings = snapshot_cache[chunks_path]
        retrieved = rank_files(
            sample,
            chunks,
            model,
            top_k=10,
            batch_size=batch_size,
            chunk_embeddings=embeddings,
        )
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
                "model": model_name,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    count = len(rows)
    return {
        "total_tasks_evaluated": count,
        "mean_recall_at_5": sum(float(row["recall_at_5"]) for row in rows) / count,
        "mean_recall_at_10": sum(float(row["recall_at_10"]) for row in rows) / count,
        "mrr": sum(float(row["reciprocal_rank"]) for row in rows) / count,
        "model": model_name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    summary = run(args.benchmark, args.corpus_dir, args.output, args.limit, args.model, args.batch_size)
    print(f"Number of tasks evaluated: {summary['total_tasks_evaluated']}")
    print(f"Mean Recall@5: {summary['mean_recall_at_5']:.4f}")
    print(f"Mean Recall@10: {summary['mean_recall_at_10']:.4f}")
    print(f"MRR: {summary['mrr']:.4f}")
    print(f"Model: {summary['model']}")
    print(f"Per-task results: {args.output}")


if __name__ == "__main__":
    main()
