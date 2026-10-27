# BM25, semantic, and hybrid retrieval: first 10 tasks

> **Validation subset only.** These results cover 10 tasks and are not a basis for final conclusions about the three methods.

## Controlled setup

All methods use the same tasks, corpus snapshots, `intent + anchor_diff` query, anchor-file exclusion, highest-scoring-chunk file deduplication, top-10 depth, and file-level gold labels. Semantic retrieval uses `sentence-transformers/all-MiniLM-L6-v2`. Hybrid retrieval applies file-level Reciprocal Rank Fusion to the saved BM25 and semantic top-10 rankings with the untuned conventional constant `k=60`.

## Aggregate results

| Method | Mean Recall@5 | Mean Recall@10 | MRR |
|---|---:|---:|---:|
| BM25 | 0.4500 | 0.6333 | 0.5917 |
| Semantic | 0.5333 | 0.5667 | 0.5000 |
| Hybrid RRF | 0.6000 | 0.6000 | 0.6833 |

## Validation observations

- Hybrid retrieval matched or exceeded both individual methods on all three metrics for 8 of the 10 tasks. It was worse than BM25 on the formatter/parser task and tied all methods at zero on the two complete-failure tasks.
- On the `default_values` task, hybrid combined semantic retrieval's two top-five gold files with a better first-relevant rank, reaching Recall@5 1.0 and reciprocal rank 1.0.
- On the snippet-parser and Tokio worker-index tasks, hybrid retained semantic retrieval's stronger early ranking. On the io-uring task, it retained BM25's full Recall@5.
- Fusion did not recover any gold file when neither input ranking contained one: all methods scored zero on the clap environment-feature task and the Caddy ECH listener-test task.
- Hybrid Recall@10 (0.6000) falls between BM25 (0.6333) and semantic retrieval (0.5667). RRF reranks only the union of the two input top-10 lists, so useful lower-ranked candidates can still be displaced.

The first-10 behavior confirms that the implementation is deterministic, excludes anchors, returns unique files, and can preserve complementary rankings. The full 58-task evaluation is required to determine whether these patterns persist.
