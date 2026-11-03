#!/usr/bin/env python3
"""Run paired Wilcoxon comparisons for the three retrieval methods."""

from __future__ import annotations

import argparse
import csv
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import wilcoxon

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = PROJECT_ROOT / "results"
METHODS = ("bm25", "semantic", "hybrid")
DISPLAY = {"bm25": "BM25", "semantic": "Semantic", "hybrid": "Hybrid RRF"}
METRICS = ("recall_at_5", "recall_at_10", "reciprocal_rank")
METRIC_DISPLAY = {"recall_at_5": "Recall@5", "recall_at_10": "Recall@10", "reciprocal_rank": "Reciprocal rank"}
ALPHA = 0.05


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def holm_adjust(p_values: list[float]) -> list[float]:
    """Return Holm-adjusted p-values in original order."""

    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [0.0] * len(p_values)
    running_max = 0.0
    total = len(p_values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (total - rank) * p_values[index])
        running_max = max(running_max, candidate)
        adjusted[index] = running_max
    return adjusted


def analyze(paths: dict[str, Path]) -> list[dict[str, Any]]:
    rows = {method: read_rows(path) for method, path in paths.items()}
    if {len(value) for value in rows.values()} != {58}:
        raise ValueError("Each method must contain exactly 58 paired tasks")
    for index in range(58):
        if len({rows[method][index]["task_id"] for method in METHODS}) != 1:
            raise ValueError(f"Task alignment mismatch at row {index + 1}")

    results: list[dict[str, Any]] = []
    applicable_indices: list[int] = []
    raw_p_values: list[float] = []
    for method_a, method_b in combinations(METHODS, 2):
        for metric in METRICS:
            values_a = np.asarray([float(row[metric]) for row in rows[method_a]], dtype=float)
            values_b = np.asarray([float(row[metric]) for row in rows[method_b]], dtype=float)
            differences = values_a - values_b
            nonzero = differences[differences != 0]
            result: dict[str, Any] = {
                "method_a": DISPLAY[method_a],
                "method_b": DISPLAY[method_b],
                "metric": METRIC_DISPLAY[metric],
                "n_pairs": len(differences),
                "n_nonzero_pairs": len(nonzero),
                "method_a_wins": int(np.sum(differences > 0)),
                "method_b_wins": int(np.sum(differences < 0)),
                "ties": int(np.sum(differences == 0)),
                "mean_difference_a_minus_b": float(np.mean(differences)),
                "median_difference_a_minus_b": float(np.median(differences)),
                "test": "Wilcoxon signed-rank, two-sided, zero_method=wilcox, asymptotic",
            }
            if len(nonzero) == 0:
                result.update(
                    {
                        "statistic": "",
                        "p_value": "",
                        "significant_at_0_05": "not_applicable",
                        "holm_adjusted_p_value": "",
                        "significant_after_holm": "not_applicable",
                        "note": "All paired differences are zero; Wilcoxon is undefined.",
                    }
                )
            else:
                test_result = wilcoxon(
                    values_a,
                    values_b,
                    zero_method="wilcox",
                    alternative="two-sided",
                    method="approx",
                )
                p_value = float(test_result.pvalue)
                result.update(
                    {
                        "statistic": float(test_result.statistic),
                        "p_value": p_value,
                        "significant_at_0_05": p_value < ALPHA,
                        "holm_adjusted_p_value": "",
                        "significant_after_holm": "",
                        "note": "Zeros are excluded; ties make the p-value asymptotic rather than exact.",
                    }
                )
                applicable_indices.append(len(results))
                raw_p_values.append(p_value)
            results.append(result)

    for result_index, adjusted_p in zip(applicable_indices, holm_adjust(raw_p_values)):
        results[result_index]["holm_adjusted_p_value"] = adjusted_p
        results[result_index]["significant_after_holm"] = adjusted_p < ALPHA
    return results


def write_outputs(results: list[dict[str, Any]], csv_path: Path, md_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    lines = [
        "# Paired statistical analysis",
        "",
        "## Method",
        "",
        "All comparisons use the same 58 tasks. A two-sided Wilcoxon signed-rank test compares paired per-task scores. Because the metrics are discrete and contain many ties, zero differences are excluded (`zero_method=wilcox`) and asymptotic p-values are reported. The test therefore evaluates the rank distribution of nonzero paired differences, not merely the difference in means.",
        "",
        "The unadjusted decision threshold is α = 0.05. Holm-adjusted p-values are also reported across the nine tests to make the multiple-comparison sensitivity explicit. Wilcoxon assumes that nonzero paired differences are approximately symmetric; given the discrete metrics and modest effective sample sizes, results should be interpreted cautiously.",
        "",
        "## Results",
        "",
        "| Comparison | Metric | W | p | Nonzero / paired | Significant (α=.05) | Holm p | Holm significant |",
        "|---|---|---:|---:|---:|---|---:|---|",
    ]
    for row in results:
        statistic = "N/A" if row["statistic"] == "" else f"{float(row['statistic']):.3f}"
        p_value = "N/A" if row["p_value"] == "" else f"{float(row['p_value']):.6f}"
        holm_p = "N/A" if row["holm_adjusted_p_value"] == "" else f"{float(row['holm_adjusted_p_value']):.6f}"
        lines.append(
            f"| {row['method_a']} vs {row['method_b']} | {row['metric']} | {statistic} | {p_value} "
            f"| {row['n_nonzero_pairs']} / {row['n_pairs']} | {row['significant_at_0_05']} "
            f"| {holm_p} | {row['significant_after_holm']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Statistical significance is determined from paired task-level differences, not from aggregate means alone. A non-significant result does not establish equivalence; it means this sample does not provide sufficient evidence of a systematic paired difference under this test. Conversely, an unadjusted p-value below 0.05 should be considered alongside the Holm result because nine related hypotheses were tested.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bm25", type=Path, default=DEFAULT_RESULTS / "bm25_edit2ripple_all.csv")
    parser.add_argument("--semantic", type=Path, default=DEFAULT_RESULTS / "semantic_edit2ripple_all.csv")
    parser.add_argument("--hybrid", type=Path, default=DEFAULT_RESULTS / "hybrid_edit2ripple_all.csv")
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_RESULTS / "statistical_analysis.csv")
    parser.add_argument("--md-output", type=Path, default=DEFAULT_RESULTS / "statistical_analysis.md")
    args = parser.parse_args()
    results = analyze({"bm25": args.bm25, "semantic": args.semantic, "hybrid": args.hybrid})
    write_outputs(results, args.csv_output, args.md_output)
    print(args.csv_output)
    print(args.md_output)


if __name__ == "__main__":
    main()
