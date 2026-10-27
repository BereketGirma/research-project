#!/usr/bin/env python3
"""Create three-method comparison data and report-ready SVG figures."""

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


def write_comparison(rows: dict[str, list[dict[str, str]]], output_path: Path) -> None:
    output_rows: list[dict[str, Any]] = []
    for index, bm25 in enumerate(rows["bm25"]):
        output: dict[str, Any] = {
            "task_id": bm25["task_id"],
            "repo": bm25["repo"],
            "base_commit": bm25["base_commit"],
            "anchor_file": bm25["anchor_file"],
            "number_of_gold_files": len(json.loads(bm25["gold_files"])),
        }
        for method in METHODS:
            for metric in METRICS:
                output[f"{method}_{metric}"] = rows[method][index][metric]
        output_rows.append(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_rows[0].keys())
        writer.writeheader()
        writer.writerows(output_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bm25", type=Path, default=DEFAULT_RESULTS / "bm25_edit2ripple_all.csv")
    parser.add_argument("--semantic", type=Path, default=DEFAULT_RESULTS / "semantic_edit2ripple_all.csv")
    parser.add_argument("--hybrid", type=Path, default=DEFAULT_RESULTS / "hybrid_edit2ripple_all.csv")
    parser.add_argument("--comparison", type=Path, default=DEFAULT_RESULTS / "all_methods_comparison.csv")
    parser.add_argument("--figures", type=Path, default=DEFAULT_RESULTS / "figures")
    args = parser.parse_args()
    rows = load_aligned({"bm25": args.bm25, "semantic": args.semantic, "hybrid": args.hybrid})
    write_comparison(rows, args.comparison)
    args.figures.mkdir(parents=True, exist_ok=True)
    figures = {
        "mean_recall_at_5_by_method.svg": mean_metric_plot(rows, "recall_at_5", "Recall@5"),
        "mean_recall_at_10_by_method.svg": mean_metric_plot(rows, "recall_at_10", "Recall@10"),
        "mean_mrr_by_method.svg": mean_metric_plot(rows, "reciprocal_rank", "MRR"),
        "per_task_method_outcomes.svg": outcome_plot(rows),
    }
    for filename, content in figures.items():
        path = args.figures / filename
        path.write_text(content, encoding="utf-8")
        print(path)
    print(args.comparison)


if __name__ == "__main__":
    main()
