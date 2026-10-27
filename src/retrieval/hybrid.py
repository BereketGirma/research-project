"""File-level Reciprocal Rank Fusion for lexical and semantic rankings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

DEFAULT_RRF_K = 60


@dataclass(frozen=True)
class HybridFileResult:
    """A file ranked by the sum of reciprocal rank contributions."""

    path: str
    score: float
    bm25_rank: int | None
    semantic_rank: int | None


def _unique_ranks(ranking: Sequence[str], anchor_file: str) -> dict[str, int]:
    """Map each non-anchor file to its first one-based rank."""

    ranks: dict[str, int] = {}
    for rank, path in enumerate(ranking, start=1):
        if path and path != anchor_file and path not in ranks:
            ranks[path] = rank
    return ranks


def reciprocal_rank_fusion(
    bm25_ranking: Sequence[str],
    semantic_ranking: Sequence[str],
    *,
    anchor_file: str = "",
    top_k: int = 10,
    rrf_k: int = DEFAULT_RRF_K,
) -> list[HybridFileResult]:
    """Fuse two file rankings using Reciprocal Rank Fusion.

    For a file ``d``, the score is::

        RRF(d) = sum_m 1 / (rrf_k + rank_m(d))

    where ``m`` is BM25 or semantic retrieval and absent files contribute
    zero. ``rrf_k=60`` is a conventional untuned constant. Exact score ties
    use lexical path order as a neutral, deterministic tie-breaker.
    """

    if top_k < 0:
        raise ValueError("top_k must be non-negative")
    if rrf_k < 0:
        raise ValueError("rrf_k must be non-negative")
    if top_k == 0:
        return []

    bm25_ranks = _unique_ranks(bm25_ranking, anchor_file)
    semantic_ranks = _unique_ranks(semantic_ranking, anchor_file)
    paths = set(bm25_ranks) | set(semantic_ranks)
    results = []
    for path in paths:
        bm25_rank = bm25_ranks.get(path)
        semantic_rank = semantic_ranks.get(path)
        score = sum(
            1.0 / (rrf_k + rank)
            for rank in (bm25_rank, semantic_rank)
            if rank is not None
        )
        results.append(HybridFileResult(path, score, bm25_rank, semantic_rank))
    results.sort(key=lambda result: (-result.score, result.path))
    return results[:top_k]
