#!/usr/bin/env python3
"""Create definitive three-method results and report-ready SVG figures."""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = PROJECT_ROOT / "results"
METHODS = ("bm25", "semantic", "hybrid")
DISPLAY_NAMES = {"bm25": "BM25", "semantic": "Semantic", "hybrid": "Hybrid RRF"}
COLORS = {"bm25": "#4472C4", "semantic": "#ED7D31", "hybrid": "#70AD47"}
METRICS = ("recall_at_5", "recall_at_10", "reciprocal_rank")

WIDTH, HEIGHT = 820, 520
LEFT, RIGHT, TOP, BOTTOM = 90, 35, 70, 80
PLOT_WIDTH, PLOT_HEIGHT = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_aligned(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    rows = {method: read_rows(path) for method, path in paths.items()}
    lengths = {len(method_rows) for method_rows in rows.values()}
    if len(lengths) != 1 or not lengths or next(iter(lengths)) == 0:
        raise ValueError("All method files must contain the same non-zero number of tasks")
    for index in range(next(iter(lengths))):
        reference = rows["bm25"][index]
        for method in METHODS[1:]:
            candidate = rows[method][index]
            for field in ("task_id", "repo", "base_commit", "anchor_file", "gold_files"):
                if reference[field] != candidate[field]:
                    raise ValueError(f"{method} mismatch at row {index + 1}: {field}")
    return rows


def svg(title: str, subtitle: str, body: list[str]) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
            '<rect width="100%" height="100%" fill="white"/>',
            '<style>text{font-family:Arial,sans-serif;fill:#202124}.title{font-size:21px;font-weight:600}.subtitle{font-size:12px;fill:#555}.label{font-size:13px}.value{font-size:13px;font-weight:600}.axis{stroke:#333}.grid{stroke:#ddd}</style>',
            f'<text x="{WIDTH/2}" y="30" text-anchor="middle" class="title">{html.escape(title)}</text>',
            f'<text x="{WIDTH/2}" y="50" text-anchor="middle" class="subtitle">{html.escape(subtitle)}</text>',
            *body,
            "</svg>",
            "",
        ]
    )


def base_axes(y_max: float, y_label: str) -> list[str]:
    parts: list[str] = []
    for step in range(6):
        value = y_max * step / 5
        y = TOP + PLOT_HEIGHT * (1 - step / 5)
        parts.extend(
            [
                f'<line x1="{LEFT}" y1="{y:.1f}" x2="{WIDTH-RIGHT}" y2="{y:.1f}" class="grid"/>',
                f'<text x="{LEFT-12}" y="{y+4:.1f}" text-anchor="end" class="label">{value:.2f}</text>',
            ]
        )
    parts.extend(
        [
            f'<line x1="{LEFT}" y1="{TOP}" x2="{LEFT}" y2="{TOP+PLOT_HEIGHT}" class="axis"/>',
            f'<line x1="{LEFT}" y1="{TOP+PLOT_HEIGHT}" x2="{WIDTH-RIGHT}" y2="{TOP+PLOT_HEIGHT}" class="axis"/>',
            f'<text x="22" y="{TOP+PLOT_HEIGHT/2}" text-anchor="middle" class="label" transform="rotate(-90 22 {TOP+PLOT_HEIGHT/2})">{html.escape(y_label)}</text>',
        ]
    )
    return parts


def mean_metric_plot(rows: dict[str, list[dict[str, str]]], metric: str, label: str) -> str:
    means = {method: sum(float(row[metric]) for row in rows[method]) / len(rows[method]) for method in METHODS}
    parts = base_axes(1.0, f"Mean {label}")
    slot = PLOT_WIDTH / len(METHODS)
    for index, method in enumerate(METHODS):
        value = means[method]
        bar_width = slot * 0.52
        x = LEFT + index * slot + (slot - bar_width) / 2
        y = TOP + PLOT_HEIGHT * (1 - value)
        parts.extend(
            [
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{TOP+PLOT_HEIGHT-y:.1f}" fill="{COLORS[method]}"/>',
                f'<text x="{x+bar_width/2:.1f}" y="{y-9:.1f}" text-anchor="middle" class="value">{value:.4f}</text>',
                f'<text x="{x+bar_width/2:.1f}" y="{TOP+PLOT_HEIGHT+26}" text-anchor="middle" class="label">{DISPLAY_NAMES[method]}</text>',
            ]
        )
    return svg(f"Mean {label} by retrieval method", f"Agent Retrieval Bench v2_edit2ripple, n={len(rows['bm25'])} tasks", parts)


def outcome_plot(rows: dict[str, list[dict[str, str]]]) -> str:
    counts = {method: Counter() for method in METHODS}
    for index in range(len(rows["bm25"])):
        for metric in METRICS:
            values = {method: float(rows[method][index][metric]) for method in METHODS}
            maximum = max(values.values())
            minimum = min(values.values())
            for method, value in values.items():
                if maximum == minimum:
                    counts[method]["all tied"] += 1
                elif value == maximum:
                    counts[method]["best"] += 1
                else:
                    counts[method]["below best"] += 1
    categories = ("best", "below best", "all tied")
    colors = {"best": "#2E7D32", "below best": "#C62828", "all tied": "#777777"}
    y_max = float(len(rows["bm25"]) * len(METRICS))
    parts = base_axes(y_max, "Task-metric outcomes")
    slot = PLOT_WIDTH / len(METHODS)
    bar_width = slot * 0.58
    for index, method in enumerate(METHODS):
        x = LEFT + index * slot + (slot - bar_width) / 2
        y_bottom = TOP + PLOT_HEIGHT
        for category in categories:
            value = counts[method][category]
            height = PLOT_HEIGHT * value / y_max
            y = y_bottom - height
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{height:.1f}" fill="{colors[category]}"><title>{category}: {value}</title></rect>')
            if height >= 20:
                parts.append(f'<text x="{x+bar_width/2:.1f}" y="{y+height/2+4:.1f}" text-anchor="middle" font-size="12" fill="white">{value}</text>')
            y_bottom = y
        parts.append(f'<text x="{x+bar_width/2:.1f}" y="{TOP+PLOT_HEIGHT+26}" text-anchor="middle" class="label">{DISPLAY_NAMES[method]}</text>')
    legend_x = LEFT
    for category in categories:
        parts.extend(
            [
                f'<rect x="{legend_x}" y="{HEIGHT-30}" width="13" height="13" fill="{colors[category]}"/>',
                f'<text x="{legend_x+19}" y="{HEIGHT-19}" class="label">{category}</text>',
            ]
        )
        legend_x += 145
    return svg(
        "Per-task metric outcomes by method",
        "Across Recall@5, Recall@10, and reciprocal rank; tied-best methods count as best unless all methods tie",
        parts,
    )


def best_methods(rows: dict[str, list[dict[str, str]]], index: int, metric: str) -> str:
    values = {method: float(rows[method][index][metric]) for method in METHODS}
    maximum = max(values.values())
    winners = [DISPLAY_NAMES[method] for method in METHODS if values[method] == maximum]
    return winners[0] if len(winners) == 1 else "Tie: " + ", ".join(winners)


def win_tie_plot(rows: dict[str, list[dict[str, str]]]) -> str:
    categories = (*METHODS, "tie")
    colors = {**COLORS, "tie": "#7F7F7F"}
    counts: dict[str, Counter[str]] = {metric: Counter() for metric in METRICS}
    for index in range(len(rows["bm25"])):
        for metric in METRICS:
            values = {method: float(rows[method][index][metric]) for method in METHODS}
            maximum = max(values.values())
            winners = [method for method, value in values.items() if value == maximum]
            counts[metric][winners[0] if len(winners) == 1 else "tie"] += 1

    parts = base_axes(float(len(rows["bm25"])), "Number of tasks")
    group_width = PLOT_WIDTH / len(METRICS)
    bar_width = group_width * 0.18
    metric_labels = {"recall_at_5": "Recall@5", "recall_at_10": "Recall@10", "reciprocal_rank": "RR"}
    for metric_index, metric in enumerate(METRICS):
        group_x = LEFT + metric_index * group_width
        for category_index, category in enumerate(categories):
            value = counts[metric][category]
            height = PLOT_HEIGHT * value / len(rows["bm25"])
            x = group_x + group_width * 0.1 + category_index * bar_width
            y = TOP + PLOT_HEIGHT - height
            parts.extend(
                [
                    f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width*0.82:.1f}" height="{height:.1f}" fill="{colors[category]}"/>',
                    f'<text x="{x+bar_width*0.41:.1f}" y="{y-6:.1f}" text-anchor="middle" class="value">{value}</text>',
                ]
            )
        parts.append(
            f'<text x="{group_x+group_width/2:.1f}" y="{TOP+PLOT_HEIGHT+26}" text-anchor="middle" class="label">{metric_labels[metric]}</text>'
        )
    legend_x = LEFT
    for category in categories:
        label = DISPLAY_NAMES.get(category, "Tied best")
        parts.extend(
            [
                f'<rect x="{legend_x}" y="{HEIGHT-30}" width="13" height="13" fill="{colors[category]}"/>',
                f'<text x="{legend_x+19}" y="{HEIGHT-19}" class="label">{label}</text>',
            ]
        )
        legend_x += 155
    return svg(
        "Unique wins and tied-best tasks by metric",
        f"Counts over {len(rows['bm25'])} paired tasks; ties include two- or three-method ties for best score",
        parts,
    )


def per_task_mrr_plot(rows: dict[str, list[dict[str, str]]]) -> str:
    parts = base_axes(1.0, "Reciprocal rank")
    slot = PLOT_WIDTH / len(METHODS)
    for method_index, method in enumerate(METHODS):
        center = LEFT + (method_index + 0.5) * slot
        for task_index, row in enumerate(rows[method]):
            value = float(row["reciprocal_rank"])
            jitter = ((task_index % 11) - 5) * 2.2
            y = TOP + PLOT_HEIGHT * (1 - value)
            parts.append(
                f'<circle cx="{center+jitter:.1f}" cy="{y:.1f}" r="3.2" fill="{COLORS[method]}" fill-opacity="0.55">'
                f'<title>Task {task_index + 1}: {value:.4f}</title></circle>'
            )
        mean = sum(float(row["reciprocal_rank"]) for row in rows[method]) / len(rows[method])
        mean_y = TOP + PLOT_HEIGHT * (1 - mean)
        parts.extend(
            [
                f'<line x1="{center-42:.1f}" y1="{mean_y:.1f}" x2="{center+42:.1f}" y2="{mean_y:.1f}" stroke="#111" stroke-width="3"/>',
                f'<text x="{center:.1f}" y="{TOP+PLOT_HEIGHT+26}" text-anchor="middle" class="label">{DISPLAY_NAMES[method]}</text>',
            ]
        )
    return svg(
        "Per-task reciprocal-rank distribution",
        "Each point is one task; horizontal black lines show method means; y-axis spans the full 0–1 range",
        parts,
    )


def write_comparison(rows: dict[str, list[dict[str, str]]], output_path: Path) -> None:
    output_rows: list[dict[str, Any]] = []
    for index, bm25 in enumerate(rows["bm25"]):
        output: dict[str, Any] = {
            "task_id": bm25["task_id"],
            "repo": bm25["repo"],
            "anchor_file": bm25["anchor_file"],
            "number_of_gold_files": len(json.loads(bm25["gold_files"])),
        }
        for metric in METRICS:
            for method in METHODS:
                output[f"{method}_{metric}"] = rows[method][index][metric]
            output[f"best_method_{metric}"] = best_methods(rows, index, metric)
        output_rows.append(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_rows[0].keys())
        writer.writeheader()
        writer.writerows(output_rows)


def write_summary(rows: dict[str, list[dict[str, str]]], output_path: Path) -> dict[str, dict[str, float]]:
    metrics = {
        method: {
            "recall_at_5": sum(float(row["recall_at_5"]) for row in rows[method]) / len(rows[method]),
            "recall_at_10": sum(float(row["recall_at_10"]) for row in rows[method]) / len(rows[method]),
            "mrr": sum(float(row["reciprocal_rank"]) for row in rows[method]) / len(rows[method]),
        }
        for method in METHODS
    }
    payload: dict[str, Any] = {
        "benchmark": "Agent Retrieval Bench v2_edit2ripple",
        "total_tasks_evaluated": len(rows["bm25"]),
        "methods": metrics,
        "semantic_model": "sentence-transformers/all-MiniLM-L6-v2",
        "hybrid": {"method": "reciprocal_rank_fusion", "rrf_k": 60, "input_depth": 10},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bm25", type=Path, default=DEFAULT_RESULTS / "bm25_edit2ripple_all.csv")
    parser.add_argument("--semantic", type=Path, default=DEFAULT_RESULTS / "semantic_edit2ripple_all.csv")
    parser.add_argument("--hybrid", type=Path, default=DEFAULT_RESULTS / "hybrid_edit2ripple_all.csv")
    parser.add_argument("--comparison", type=Path, default=DEFAULT_RESULTS / "final_retrieval_comparison.csv")
    parser.add_argument("--summary", type=Path, default=DEFAULT_RESULTS / "final_retrieval_summary.json")
    parser.add_argument("--figures", type=Path, default=DEFAULT_RESULTS / "figures")
    args = parser.parse_args()
    rows = load_aligned({"bm25": args.bm25, "semantic": args.semantic, "hybrid": args.hybrid})
    write_comparison(rows, args.comparison)
    summary = write_summary(rows, args.summary)
    args.figures.mkdir(parents=True, exist_ok=True)
    figures = {
        "mean_recall_at_5_by_method.svg": mean_metric_plot(rows, "recall_at_5", "Recall@5"),
        "mean_recall_at_10_by_method.svg": mean_metric_plot(rows, "recall_at_10", "Recall@10"),
        "mean_mrr_by_method.svg": mean_metric_plot(rows, "reciprocal_rank", "MRR"),
        "per_task_method_outcomes.svg": outcome_plot(rows),
        "win_tie_counts_by_metric.svg": win_tie_plot(rows),
        "per_task_mrr_distribution.svg": per_task_mrr_plot(rows),
    }
    for filename, content in figures.items():
        path = args.figures / filename
        path.write_text(content, encoding="utf-8")
        print(path)
    print(args.comparison)
    print(args.summary)
    print("\nMethod       Recall@5  Recall@10  MRR")
    for method in METHODS:
        values = summary[method]
        print(
            f"{DISPLAY_NAMES[method]:<12} "
            f"{values['recall_at_5']:.4f}    {values['recall_at_10']:.4f}     {values['mrr']:.4f}"
        )


if __name__ == "__main__":
    main()
