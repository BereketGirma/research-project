#!/usr/bin/env python3
"""Generate simple, dependency-free SVG plots for retrieval results."""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "results/bm25_edit2ripple_all.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results/figures"

WIDTH, HEIGHT = 900, 520
MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM = 85, 35, 55, 75
PLOT_WIDTH = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PLOT_HEIGHT = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM


def svg_document(title: str, body: Iterable[str]) -> str:
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222}.axis{stroke:#333;stroke-width:1}.grid{stroke:#ddd;stroke-width:1}.bar{fill:#477aa8}.point{fill:#b24c3d}.label{font-size:12px}.title{font-size:20px;font-weight:600}</style>',
        f'<text x="{WIDTH / 2}" y="30" text-anchor="middle" class="title">{html.escape(title)}</text>',
        *body,
        "</svg>",
    ]
    return "\n".join(elements) + "\n"


def axes(y_max: float, y_label: str, x_label: str) -> list[str]:
    parts: list[str] = []
    for step in range(6):
        value = y_max * step / 5
        y = MARGIN_TOP + PLOT_HEIGHT - PLOT_HEIGHT * step / 5
        parts.append(f'<line x1="{MARGIN_LEFT}" y1="{y:.1f}" x2="{WIDTH-MARGIN_RIGHT}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{MARGIN_LEFT-10}" y="{y+4:.1f}" text-anchor="end" class="label">{value:.1f}</text>')
    parts.extend(
        [
            f'<line x1="{MARGIN_LEFT}" y1="{MARGIN_TOP}" x2="{MARGIN_LEFT}" y2="{MARGIN_TOP+PLOT_HEIGHT}" class="axis"/>',
            f'<line x1="{MARGIN_LEFT}" y1="{MARGIN_TOP+PLOT_HEIGHT}" x2="{WIDTH-MARGIN_RIGHT}" y2="{MARGIN_TOP+PLOT_HEIGHT}" class="axis"/>',
            f'<text x="{WIDTH/2}" y="{HEIGHT-20}" text-anchor="middle" class="label">{html.escape(x_label)}</text>',
            f'<text x="18" y="{HEIGHT/2}" text-anchor="middle" class="label" transform="rotate(-90 18 {HEIGHT/2})">{html.escape(y_label)}</text>',
        ]
    )
    return parts


def distribution_plot(values: list[float], metric: str) -> str:
    counts = Counter(values)
    categories = sorted(counts)
    y_max = max(counts.values())
    parts = axes(float(y_max), "Number of tasks", metric)
    slot = PLOT_WIDTH / max(1, len(categories))
    for index, value in enumerate(categories):
        height = PLOT_HEIGHT * counts[value] / y_max
        x = MARGIN_LEFT + index * slot + slot * 0.15
        y = MARGIN_TOP + PLOT_HEIGHT - height
        width = slot * 0.7
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" class="bar"/>')
        parts.append(f'<text x="{x+width/2:.1f}" y="{MARGIN_TOP+PLOT_HEIGHT+20}" text-anchor="middle" class="label">{value:.2f}</text>')
        parts.append(f'<text x="{x+width/2:.1f}" y="{y-6:.1f}" text-anchor="middle" class="label">{counts[value]}</text>')
    return svg_document(f"Distribution of {metric}", parts)


def reciprocal_rank_plot(values: list[float]) -> str:
    parts = axes(1.0, "Reciprocal rank", "Task index (benchmark order)")
    for index, value in enumerate(values, start=1):
        x = MARGIN_LEFT + (index - 0.5) * PLOT_WIDTH / len(values)
        y = MARGIN_TOP + PLOT_HEIGHT * (1 - value)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="point"><title>Task {index}: {value:.4f}</title></circle>')
    for tick in range(0, len(values) + 1, 5):
        if tick == 0:
            continue
        x = MARGIN_LEFT + (tick - 0.5) * PLOT_WIDTH / len(values)
        parts.append(f'<text x="{x:.1f}" y="{MARGIN_TOP+PLOT_HEIGHT+20}" text-anchor="middle" class="label">{tick}</text>')
    return svg_document("Per-task reciprocal rank", parts)


def repository_plot(rows: list[dict[str, str]], minimum_samples: int = 3) -> str | None:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[row["repo"]].append(float(row["reciprocal_rank"]))
    grouped = {repo: values for repo, values in grouped.items() if len(values) >= minimum_samples}
    if len(grouped) < 2:
        return None
    categories = sorted(grouped)
    means = [sum(grouped[repo]) / len(grouped[repo]) for repo in categories]
    parts = axes(1.0, "Mean reciprocal rank", f"Repository (minimum n={minimum_samples})")
    slot = PLOT_WIDTH / len(categories)
    for index, (repo, mean) in enumerate(zip(categories, means)):
        height = PLOT_HEIGHT * mean
        x = MARGIN_LEFT + index * slot + slot * 0.15
        y = MARGIN_TOP + PLOT_HEIGHT - height
        width = slot * 0.7
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" class="bar"/>')
        label = f"{repo} (n={len(grouped[repo])})"
        parts.append(f'<text x="{x+width/2:.1f}" y="{MARGIN_TOP+PLOT_HEIGHT+12}" text-anchor="end" class="label" transform="rotate(-30 {x+width/2:.1f} {MARGIN_TOP+PLOT_HEIGHT+12})">{html.escape(label)}</text>')
    return svg_document("BM25 mean reciprocal rank by repository", parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"No rows found in {args.input}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "bm25_recall_at_5_distribution.svg": distribution_plot([float(row["recall_at_5"]) for row in rows], "Recall@5"),
        "bm25_recall_at_10_distribution.svg": distribution_plot([float(row["recall_at_10"]) for row in rows], "Recall@10"),
        "bm25_reciprocal_rank_by_task.svg": reciprocal_rank_plot([float(row["reciprocal_rank"]) for row in rows]),
    }
    repo_svg = repository_plot(rows)
    if repo_svg is not None:
        outputs["bm25_mrr_by_repository.svg"] = repo_svg
    for filename, content in outputs.items():
        (args.output_dir / filename).write_text(content, encoding="utf-8")
        print(args.output_dir / filename)


if __name__ == "__main__":
    main()
