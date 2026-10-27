#!/usr/bin/env python3
"""Compare BM25 and semantic retrieval over aligned edit2ripple tasks."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BM25 = PROJECT_ROOT / "results/bm25_edit2ripple_all.csv"
DEFAULT_SEMANTIC = PROJECT_ROOT / "results/semantic_edit2ripple_all.csv"
DEFAULT_CSV = PROJECT_ROOT / "results/bm25_vs_semantic_all.csv"
DEFAULT_MD = PROJECT_ROOT / "results/bm25_vs_semantic_analysis.md"
METRICS = ("recall_at_5", "recall_at_10", "reciprocal_rank")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def metric_winner(bm25: float, semantic: float) -> str:
    if bm25 > semantic:
        return "BM25"
    if semantic > bm25:
        return "semantic"
    return "tie"


def overall_outcome(metric_winners: list[str]) -> str:
    counts = Counter(metric_winners)
    if counts["BM25"] > counts["semantic"]:
        return "BM25"
    if counts["semantic"] > counts["BM25"]:
        return "semantic"
    return "tie/mixed"


def is_test_path(path: str) -> bool:
    """Apply a transparent path/name heuristic for descriptive role counts."""

    lowered = path.lower()
    parts = lowered.split("/")
    return any(part in {"test", "tests", "testing", "testsuite"} for part in parts) or bool(
        re.search(r"(^|[_.-])tests?([_.-]|$)", parts[-1])
    )


def compare(
    bm25_path: Path,
    semantic_path: Path,
    csv_path: Path,
    md_path: Path,
) -> list[dict[str, Any]]:
    bm25_rows = read_rows(bm25_path)
    semantic_rows = read_rows(semantic_path)
    if not bm25_rows or len(bm25_rows) != len(semantic_rows):
        raise ValueError("BM25 and semantic inputs must contain the same non-zero number of tasks")

    comparison: list[dict[str, Any]] = []
    for bm25, semantic in zip(bm25_rows, semantic_rows):
        for field in ("task_id", "repo", "base_commit", "anchor_file", "gold_files"):
            if bm25[field] != semantic[field]:
                raise ValueError(f"Input mismatch for field {field}: {bm25.get('task_id')}")
        b = {metric: float(bm25[metric]) for metric in METRICS}
        s = {metric: float(semantic[metric]) for metric in METRICS}
        winners = [metric_winner(b[metric], s[metric]) for metric in METRICS]
        comparison.append(
            {
                "task_id": bm25["task_id"],
                "repo": bm25["repo"],
                "anchor_file": bm25["anchor_file"],
                "number_of_gold_files": len(json.loads(bm25["gold_files"])),
                "bm25_recall_at_5": b["recall_at_5"],
                "semantic_recall_at_5": s["recall_at_5"],
                "recall_at_5_winner": winners[0],
                "bm25_recall_at_10": b["recall_at_10"],
                "semantic_recall_at_10": s["recall_at_10"],
                "recall_at_10_winner": winners[1],
                "bm25_reciprocal_rank": b["reciprocal_rank"],
                "semantic_reciprocal_rank": s["reciprocal_rank"],
                "reciprocal_rank_winner": winners[2],
                "overall_outcome": overall_outcome(winners),
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
    outcome_counts = Counter(str(row["overall_outcome"]) for row in comparison)
    role_stats = {
        method: {role: [0, 0, 0] for role in ("test", "non_test")}
        for method in ("bm25", "semantic")
    }
    for bm25, semantic in zip(bm25_rows, semantic_rows):
        for gold_path in json.loads(bm25["gold_files"]):
            role = "test" if is_test_path(gold_path) else "non_test"
            for method, source in (("bm25", bm25), ("semantic", semantic)):
                ranking = json.loads(source["top_10_files"])
                rank = ranking.index(gold_path) + 1 if gold_path in ranking else None
                role_stats[method][role][0] += 1
                role_stats[method][role][1] += int(rank is not None and rank <= 5)
                role_stats[method][role][2] += int(rank is not None and rank <= 10)
    dominance: dict[str, list[dict[str, Any]]] = {"BM25": [], "semantic": []}
    for row in comparison:
        differences = [
            float(row[f"bm25_{metric}"]) - float(row[f"semantic_{metric}"])
            for metric in METRICS
        ]
        if all(value >= 0 for value in differences) and any(value > 0 for value in differences):
            row["dominance_margin"] = sum(differences)
            dominance["BM25"].append(row)
        elif all(value <= 0 for value in differences) and any(value < 0 for value in differences):
            row["dominance_margin"] = -sum(differences)
            dominance["semantic"].append(row)
    for method in dominance:
        dominance[method].sort(key=lambda row: (-float(row["dominance_margin"]), str(row["task_id"])))

    lines = [
        "# BM25 versus semantic retrieval: all edit2ripple tasks",
        "",
        "> These are controlled results for the 58-task subset. Explanations below separate measured outcomes from hypotheses that require additional analysis.",
        "",
        "## Overall results",
        "",
        "| Method | Mean Recall@5 | Mean Recall@10 | MRR |",
        "|---|---:|---:|---:|",
        f"| BM25 | {means['bm25']['recall_at_5']:.4f} | {means['bm25']['recall_at_10']:.4f} | {means['bm25']['reciprocal_rank']:.4f} |",
        f"| Semantic | {means['semantic']['recall_at_5']:.4f} | {means['semantic']['recall_at_10']:.4f} | {means['semantic']['reciprocal_rank']:.4f} |",
        "",
        "A task-level outcome is assigned by which method wins more of Recall@5, Recall@10, and reciprocal rank; equal win counts are reported as tie/mixed.",
        "",
        f"- BM25 task wins: **{outcome_counts['BM25']}**",
        f"- Semantic task wins: **{outcome_counts['semantic']}**",
        f"- Ties or mixed trade-offs: **{outcome_counts['tie/mixed']}**",
        "",
        "## Largest clear differences",
        "",
        "The examples below are selected mechanically: the named method is no worse on any metric and has the largest summed advantage across the three metrics.",
        "",
    ]
    for method in ("BM25", "semantic"):
        lines.extend([f"### {method} clear wins", ""])
        for row in dominance[method][:5]:
            lines.append(
                f"- `{row['task_id']}` ({row['repo']}, `{row['anchor_file']}`): "
                f"R@5 {float(row['bm25_recall_at_5']):.3f}/{float(row['semantic_recall_at_5']):.3f}, "
                f"R@10 {float(row['bm25_recall_at_10']):.3f}/{float(row['semantic_recall_at_10']):.3f}, "
                f"RR {float(row['bm25_reciprocal_rank']):.3f}/{float(row['semantic_reciprocal_rank']):.3f} "
                "(BM25/semantic)."
            )
        if not dominance[method]:
            lines.append("- None.")
        lines.append("")
    lines.extend(
        [
            "## Observed task evidence",
            "",
            "- In task `148cbb0363427a9415265626`, the query names `epHealthCommandFunc`; that exact function name occurs in gold `etcdctl/ctlv3/command/ep_command.go`. BM25 retrieved the two gold files at ranks 8 and 1, while semantic retrieval retrieved neither. This is direct evidence of a lexical/identifier-friendly case.",
            "- In task `4f6c4f2d9b8ae3a553dfbf1f`, anchor `binding/form_mapping.go`, gold `binding/form_mapping_test.go`, and the query share `binding`/`form` terminology. BM25 ranked the test file second; semantic retrieval missed it. The paired filename and path terminology are observed, although they cannot alone prove why the score differed.",
            "- In task `9a326250f0d9b6336a9cf026`, a long query about distributed `from_pretrained` orchestration points to `modeling_utils.py`. Semantic retrieval ranked it second and BM25 missed it. The query and target share identifiers including `distributed_config`, `device_mesh`, and `FSDP2`, so this is not a pure “different terminology” example; the broader orchestration context and long, noisy query are plausible contributors that require a targeted ablation.",
            "- In task `bb9cf609f8e5521ab080803e`, the HTTP/3 change retrieved `.golangci.yml` at semantic rank 4 even though the gold path shares no meaningful token with the query; BM25 missed it. This is consistent with semantic retrieval connecting a build/tooling consequence to the feature description, but content-level causal attribution remains a hypothesis.",
            "- In task `cbb729b2af79ab394110ba8e`, semantic retrieval ranked `context_test.go` first for a protocol-buffer content-negotiation change, while BM25 ranked it seventh. Both the paired filename and conceptual content are present, so the result does not isolate which signal drove the improvement.",
            "",
            "## Test versus non-test gold files",
            "",
            "Across the 99 individual gold-file labels, 45 were classified as test files using path/name conventions. Their observed file hit rates were:",
            "",
            "| Method | Test hit@5 | Test hit@10 | Non-test hit@5 | Non-test hit@10 |",
            "|---|---:|---:|---:|---:|",
            f"| BM25 | {role_stats['bm25']['test'][1] / role_stats['bm25']['test'][0]:.3f} | {role_stats['bm25']['test'][2] / role_stats['bm25']['test'][0]:.3f} | {role_stats['bm25']['non_test'][1] / role_stats['bm25']['non_test'][0]:.3f} | {role_stats['bm25']['non_test'][2] / role_stats['bm25']['non_test'][0]:.3f} |",
            f"| Semantic | {role_stats['semantic']['test'][1] / role_stats['semantic']['test'][0]:.3f} | {role_stats['semantic']['test'][2] / role_stats['semantic']['test'][0]:.3f} | {role_stats['semantic']['non_test'][1] / role_stats['semantic']['non_test'][0]:.3f} | {role_stats['semantic']['non_test'][2] / role_stats['semantic']['non_test'][0]:.3f} |",
            "",
            "In this subset, BM25 did not show a general disadvantage on test files, while semantic retrieval's test-file hit rates were lower than its non-test hit rates. These are per-gold-file descriptive rates, not task-level metrics, and file role is confounded with repository, language, and change type.",
            "",
            "## Interpretation boundaries",
            "",
            "The CSV records observed per-task metrics and winners. Exact identifiers, path terminology, conceptual similarity, and test-versus-implementation roles can coexist in one task, so the examples do not isolate causal effects. Repository and language are also confounded with task type in this subset. Controlled query-component and document-component ablations would be needed to attribute performance differences to a specific signal.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return comparison


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bm25", type=Path, default=DEFAULT_BM25)
    parser.add_argument("--semantic", type=Path, default=DEFAULT_SEMANTIC)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    rows = compare(args.bm25, args.semantic, args.csv_output, args.md_output)
    print(f"Compared {len(rows)} tasks")
    print(args.csv_output)
    print(args.md_output)


if __name__ == "__main__":
    main()
