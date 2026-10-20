#!/usr/bin/env python3
"""Compare directly comparable BM25 and semantic first-10 results."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BM25 = PROJECT_ROOT / "results/bm25_edit2ripple_first10.csv"
DEFAULT_SEMANTIC = PROJECT_ROOT / "results/semantic_edit2ripple_first10.csv"
DEFAULT_CSV = PROJECT_ROOT / "results/bm25_vs_semantic_first10.csv"
DEFAULT_MD = PROJECT_ROOT / "results/bm25_vs_semantic_first10.md"
METRICS = ("recall_at_5", "recall_at_10", "reciprocal_rank")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def compare(bm25_path: Path, semantic_path: Path, csv_path: Path, md_path: Path) -> None:
    bm25_rows = read_rows(bm25_path)
    semantic_rows = read_rows(semantic_path)
    if len(bm25_rows) != len(semantic_rows):
        raise ValueError("BM25 and semantic result files have different row counts")
    semantic_by_id = {row["task_id"]: row for row in semantic_rows}
    comparison: list[dict[str, str | float]] = []
    for bm25 in bm25_rows:
        semantic = semantic_by_id.get(bm25["task_id"])
        if semantic is None:
            raise ValueError(f"Semantic results are missing task {bm25['task_id']}")
        for field in ("repo", "base_commit", "anchor_file", "gold_files"):
            if bm25[field] != semantic[field]:
                raise ValueError(f"Methodology mismatch for {bm25['task_id']}: {field}")
        bm25_values = [float(bm25[metric]) for metric in METRICS]
        semantic_values = [float(semantic[metric]) for metric in METRICS]
        bm25_wins = sum(a > b for a, b in zip(bm25_values, semantic_values))
        semantic_wins = sum(b > a for a, b in zip(bm25_values, semantic_values))
        if bm25_wins > semantic_wins:
            outcome = "BM25 better"
        elif semantic_wins > bm25_wins:
            outcome = "Semantic better"
        else:
            outcome = "Tie"
        comparison.append(
            {
                "task_id": bm25["task_id"],
                "repo": bm25["repo"],
                "anchor_file": bm25["anchor_file"],
                "bm25_recall_at_5": bm25_values[0],
                "semantic_recall_at_5": semantic_values[0],
                "bm25_recall_at_10": bm25_values[1],
                "semantic_recall_at_10": semantic_values[1],
                "bm25_reciprocal_rank": bm25_values[2],
                "semantic_reciprocal_rank": semantic_values[2],
                "overall_outcome": outcome,
            }
        )

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=comparison[0].keys())
        writer.writeheader()
        writer.writerows(comparison)

    means = {
        method: {
            metric: sum(float(row[f"{method}_{metric}"]) for row in comparison) / len(comparison)
            for metric in METRICS
        }
        for method in ("bm25", "semantic")
    }
    groups = {
        outcome: [str(row["task_id"]) for row in comparison if row["overall_outcome"] == outcome]
        for outcome in ("BM25 better", "Semantic better", "Tie")
    }
    lines = [
        "# BM25 vs semantic retrieval: first 10 tasks",
        "",
        "> **Preliminary:** this comparison covers only 10 tasks and does not establish that either method is definitively better.",
        "",
        "Both methods use the same tasks and snapshots, `intent + anchor_diff` query, `path + symbol + chunk text` documents, anchor-file exclusion, highest-scoring-chunk file deduplication, top-10 depth, and file-level gold labels. The semantic model is `sentence-transformers/all-MiniLM-L6-v2`.",
        "",
        "## Aggregate metrics",
        "",
        "| Method | Mean Recall@5 | Mean Recall@10 | MRR |",
        "|---|---:|---:|---:|",
        f"| BM25 | {means['bm25']['recall_at_5']:.4f} | {means['bm25']['recall_at_10']:.4f} | {means['bm25']['reciprocal_rank']:.4f} |",
        f"| Semantic | {means['semantic']['recall_at_5']:.4f} | {means['semantic']['recall_at_10']:.4f} | {means['semantic']['reciprocal_rank']:.4f} |",
        "",
        "## Per-task comparison",
        "",
        "| Task | R@5 BM25 / semantic | R@10 BM25 / semantic | RR BM25 / semantic | Outcome |",
        "|---|---:|---:|---:|---|",
    ]
    for row in comparison:
        lines.append(
            f"| `{row['task_id']}` | {float(row['bm25_recall_at_5']):.3f} / {float(row['semantic_recall_at_5']):.3f} "
            f"| {float(row['bm25_recall_at_10']):.3f} / {float(row['semantic_recall_at_10']):.3f} "
            f"| {float(row['bm25_reciprocal_rank']):.3f} / {float(row['semantic_reciprocal_rank']):.3f} "
            f"| {row['overall_outcome']} |"
        )
    lines.extend(["", "## Outcome groups", ""])
    for outcome, task_ids in groups.items():
        rendered = ", ".join(f"`{task_id}`" for task_id in task_ids) if task_ids else "None"
        lines.append(f"- **{outcome}:** {rendered}")
    lines.extend(
        [
            "",
            "## Preliminary interpretation",
            "",
            "- Both methods performed perfectly on the metrics/route task and both missed every gold file on the clap environment-feature task and the Caddy ECH listener test task. Semantic similarity did not automatically recover the two difficult low-recall cases.",
            "- BM25 was clearly stronger on the Caddy formatter/parser task: it found `parse.go` at rank 1 and `formatter_test.go` at rank 8, while semantic retrieval found none of its three gold files. BM25 also placed all three exact-identifier-heavy Tokio io-uring files in the top 3; semantic retrieval moved `fs/write.rs` to rank 6, although both reached full Recall@10.",
            "- Semantic retrieval moved the Caddy snippet parser test from rank 6 to rank 3 and moved the two retrieved Tokio worker-index files from ranks 4/5 to ranks 1/2. These are examples where its ranking favored contextually related files more strongly.",
            "- The `default_values` task is a metric tradeoff rather than a clean method win: semantic retrieval moved both gold files into the top 5 (ranks 3 and 5 versus BM25 ranks 2 and 9), raising Recall@5, while BM25 retained the better reciprocal rank.",
            "- Overall, semantic retrieval has higher mean Recall@5 in this sample, while BM25 has higher mean Recall@10 and MRR. This suggests different ranking behavior, not a definitive winner.",
            "",
            "These ten cases should be treated as diagnostic examples: repository, language, change type, and gold-file role are confounded in such a small sample. A full-dataset paired run and error analysis are needed before making a comparative research claim.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bm25", type=Path, default=DEFAULT_BM25)
    parser.add_argument("--semantic", type=Path, default=DEFAULT_SEMANTIC)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    compare(args.bm25, args.semantic, args.csv_output, args.md_output)
    print(args.csv_output)
    print(args.md_output)


if __name__ == "__main__":
    main()
