"""Chunk-scored, file-level semantic retrieval for edit2ripple."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol, Sequence

import numpy as np
from numpy.typing import NDArray

from retrieval.bm25 import build_query, searchable_text

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class Encoder(Protocol):
    """The subset of SentenceTransformer used by this retriever."""

    def encode(self, sentences: str | list[str], **kwargs: Any) -> NDArray[np.floating[Any]]: ...


@dataclass(frozen=True)
class SemanticFileResult:
    """The highest-scoring semantic chunk representing a file."""

    path: str
    score: float
    chunk_id: str


def load_model(model_name: str = DEFAULT_MODEL_NAME, device: str = "cpu") -> Encoder:
    """Load the documented sentence-transformer lazily."""

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name, device=device, trust_remote_code=False)


def encode_chunks(
    chunks: Sequence[dict[str, Any]],
    model: Encoder,
    batch_size: int = 64,
) -> NDArray[np.floating[Any]]:
    """Encode path + symbol + chunk text into normalized document vectors."""

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    documents = [searchable_text(chunk) for chunk in chunks]
    if not documents:
        return np.empty((0, 0), dtype=np.float32)
    return np.asarray(
        model.encode(
            documents,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    )


def rank_files(
    sample: dict[str, Any],
    chunks: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
    model: Encoder,
    top_k: int = 10,
    batch_size: int = 64,
    chunk_embeddings: NDArray[np.floating[Any]] | None = None,
) -> list[SemanticFileResult]:
    """Rank chunks by cosine similarity and keep the best chunk per file.

    Supplied embeddings must correspond one-to-one with ``chunks``. This lets
    an experiment reuse a snapshot's document embeddings for multiple tasks;
    anchor-file chunks are still excluded before ranking.
    """

    if top_k < 0:
        raise ValueError("top_k must be non-negative")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    all_chunks = list(chunks)
    if not all_chunks or top_k == 0:
        return []

    if chunk_embeddings is None:
        embeddings = encode_chunks(all_chunks, model, batch_size=batch_size)
    else:
        embeddings = np.asarray(chunk_embeddings)
        if len(embeddings) != len(all_chunks):
            raise ValueError("chunk_embeddings must correspond one-to-one with chunks")

    query_text = build_query(sample)
    query_embedding = np.asarray(
        model.encode(
            query_text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    ).reshape(-1)
    if embeddings.ndim != 2 or embeddings.shape[1] != query_embedding.shape[0]:
        raise ValueError("Document and query embedding dimensions do not match")

    anchor_file = str((sample.get("query") or {}).get("anchor_file") or "")
    candidate_indices = [
        index
        for index, chunk in enumerate(all_chunks)
        if str(chunk.get("path") or "") != anchor_file
    ]
    if not candidate_indices:
        return []

    scores = embeddings @ query_embedding
    # Stable corpus-order tie breaking matches the BM25 baseline.
    ranked_indices = sorted(candidate_indices, key=lambda index: (-float(scores[index]), index))
    results: list[SemanticFileResult] = []
    seen_paths: set[str] = set()
    for index in ranked_indices:
        chunk = all_chunks[index]
        path = str(chunk.get("path") or "")
        if not path or path in seen_paths:
            continue
        seen_paths.add(path)
        results.append(
            SemanticFileResult(
                path=path,
                score=float(scores[index]),
                chunk_id=str(chunk.get("chunk_id") or ""),
            )
        )
        if len(results) == top_k:
            break
    return results
