"""A small, file-level BM25 baseline for edit2ripple.

BM25 scores corpus chunks. The public result is deliberately file-level,
because edit2ripple's gold labels are file paths rather than chunk IDs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from rank_bm25 import BM25Okapi

ALPHANUMERIC_RE = re.compile(r"[A-Za-z0-9]+")
CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
ACRONYM_BOUNDARY_RE = re.compile(r"(?<=[A-Z])(?=[A-Z][a-z])")


@dataclass(frozen=True)
class FileResult:
    """The best-scoring chunk representing one retrieved file."""

    path: str
    score: float
    chunk_id: str


@dataclass(frozen=True)
class TaskMetrics:
    recall_at_5: float
    recall_at_10: float
    reciprocal_rank: float


def tokenize(text: str) -> list[str]:
    """Lowercase and split camelCase, snake_case, and non-alphanumerics."""

    # Handle both ordinary camelCase ("anchorFile") and acronym transitions
    # ("HTTPServer" -> "HTTP Server") before treating underscores as spaces.
    text = ACRONYM_BOUNDARY_RE.sub(" ", str(text))
    text = CAMEL_BOUNDARY_RE.sub(" ", text)
    text = text.replace("_", " ")
    return [match.group(0).lower() for match in ALPHANUMERIC_RE.finditer(text)]


def build_query(sample: dict[str, Any]) -> str:
    """Build the lexical query from exactly intent and anchor_diff."""

    query = sample.get("query") or {}
    return "\n".join(str(query.get(field) or "") for field in ("intent", "anchor_diff"))


def searchable_text(chunk: dict[str, Any]) -> str:
    """Build a BM25 document from exactly path, symbol, and chunk text."""

    return "\n".join(str(chunk.get(field) or "") for field in ("path", "symbol", "text"))


def candidate_chunks(sample: dict[str, Any], chunks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return valid candidates after removing every anchor-file chunk.

    The anchor file is already provided to the task, so allowing any of its
    chunks into retrieval would spend result capacity on known context and
    would not measure ripple-file discovery.
    """

    anchor_file = str((sample.get("query") or {}).get("anchor_file") or "")
    return [chunk for chunk in chunks if str(chunk.get("path") or "") != anchor_file]


def rank_files(
    sample: dict[str, Any],
    chunks: Iterable[dict[str, Any]],
    top_k: int = 10,
) -> list[FileResult]:
    """Score chunks with BM25 and retain the best-ranked chunk per file."""

    if top_k < 0:
        raise ValueError("top_k must be non-negative")

    candidates = candidate_chunks(sample, chunks)
    if not candidates or top_k == 0:
        return []

    documents = [tokenize(searchable_text(chunk)) for chunk in candidates]
    query_tokens = tokenize(build_query(sample))
    bm25 = BM25Okapi(documents)
    scores = bm25.get_scores(query_tokens)

    # Ties retain corpus order for deterministic runs. Once chunks are ranked,
    # the first occurrence is the highest-scoring chunk for that path.
    ranked_indices = sorted(range(len(candidates)), key=lambda index: (-float(scores[index]), index))
    results: list[FileResult] = []
    seen_paths: set[str] = set()
    for index in ranked_indices:
        chunk = candidates[index]
        path = str(chunk.get("path") or "")
        if not path or path in seen_paths:
            continue

        # Gold labels are file paths, so duplicate chunks must not consume
        # multiple result positions. Keep only each file's best-ranked chunk.
        seen_paths.add(path)
        results.append(
            FileResult(
                path=path,
                score=float(scores[index]),
                chunk_id=str(chunk.get("chunk_id") or ""),
            )
        )
        if len(results) == top_k:
            break
    return results


def evaluate_ranking(gold_files: Sequence[str], ranked_files: Sequence[str]) -> TaskMetrics:
    """Compute file recall and reciprocal rank over the retrieved ranking."""

    gold = set(gold_files)
    if not gold:
        return TaskMetrics(0.0, 0.0, 0.0)

    recall_at_5 = len(gold.intersection(ranked_files[:5])) / len(gold)
    recall_at_10 = len(gold.intersection(ranked_files[:10])) / len(gold)
    reciprocal_rank = 0.0
    for rank, path in enumerate(ranked_files, start=1):
        if path in gold:
            reciprocal_rank = 1.0 / rank
            break
    return TaskMetrics(recall_at_5, recall_at_10, reciprocal_rank)
