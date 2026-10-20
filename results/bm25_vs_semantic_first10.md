# BM25 vs semantic retrieval: first 10 tasks

> **Preliminary:** this comparison covers only 10 tasks and does not establish that either method is definitively better.

Both methods use the same tasks and snapshots, `intent + anchor_diff` query, `path + symbol + chunk text` documents, anchor-file exclusion, highest-scoring-chunk file deduplication, top-10 depth, and file-level gold labels. The semantic model is `sentence-transformers/all-MiniLM-L6-v2`.

## Aggregate metrics

| Method | Mean Recall@5 | Mean Recall@10 | MRR |
|---|---:|---:|---:|
| BM25 | 0.4500 | 0.6333 | 0.5917 |
| Semantic | 0.5333 | 0.5667 | 0.5000 |

## Per-task comparison

| Task | R@5 BM25 / semantic | R@10 BM25 / semantic | RR BM25 / semantic | Outcome |
|---|---:|---:|---:|---|
| `365be40339d415a67237eee9` | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | Tie |
| `7a8ae85f26f7972e3c50c14c` | 0.500 / 0.500 | 0.500 / 0.500 | 1.000 / 0.333 | BM25 better |
| `a726f272e7ddbd50bac4face` | 0.500 / 0.500 | 0.500 / 0.500 | 1.000 / 1.000 | Tie |
| `f0e2f6c47c53aab117eca775` | 0.333 / 0.000 | 0.667 / 0.000 | 1.000 / 0.000 | BM25 better |
| `30fded9a7b09048b5c8f39de` | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | Tie |
| `8b6ab1ba0883ff8104d28524` | 0.500 / 1.000 | 1.000 / 1.000 | 0.500 / 0.333 | Tie |
| `88f4b3f165035260aec813d3` | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 | Tie |
| `0631449332f969f725276ef8` | 0.000 / 1.000 | 1.000 / 1.000 | 0.167 / 0.333 | Semantic better |
| `a4bb43c519262529c3cd0ddf` | 1.000 / 0.667 | 1.000 / 1.000 | 1.000 / 1.000 | BM25 better |
| `18a155cebfee9969b166934c` | 0.667 / 0.667 | 0.667 / 0.667 | 0.250 / 1.000 | Semantic better |

## Outcome groups

- **BM25 better:** `7a8ae85f26f7972e3c50c14c`, `f0e2f6c47c53aab117eca775`, `a4bb43c519262529c3cd0ddf`
- **Semantic better:** `0631449332f969f725276ef8`, `18a155cebfee9969b166934c`
- **Tie:** `365be40339d415a67237eee9`, `a726f272e7ddbd50bac4face`, `30fded9a7b09048b5c8f39de`, `8b6ab1ba0883ff8104d28524`, `88f4b3f165035260aec813d3`

## Preliminary interpretation

- Both methods performed perfectly on the metrics/route task and both missed every gold file on the clap environment-feature task and the Caddy ECH listener test task. Semantic similarity did not automatically recover the two difficult low-recall cases.
- BM25 was clearly stronger on the Caddy formatter/parser task: it found `parse.go` at rank 1 and `formatter_test.go` at rank 8, while semantic retrieval found none of its three gold files. BM25 also placed all three exact-identifier-heavy Tokio io-uring files in the top 3; semantic retrieval moved `fs/write.rs` to rank 6, although both reached full Recall@10.
- Semantic retrieval moved the Caddy snippet parser test from rank 6 to rank 3 and moved the two retrieved Tokio worker-index files from ranks 4/5 to ranks 1/2. These are examples where its ranking favored contextually related files more strongly.
- The `default_values` task is a metric tradeoff rather than a clean method win: semantic retrieval moved both gold files into the top 5 (ranks 3 and 5 versus BM25 ranks 2 and 9), raising Recall@5, while BM25 retained the better reciprocal rank.
- Overall, semantic retrieval has higher mean Recall@5 in this sample, while BM25 has higher mean Recall@10 and MRR. This suggests different ranking behavior, not a definitive winner.

These ten cases should be treated as diagnostic examples: repository, language, change type, and gold-file role are confounded in such a small sample. A full-dataset paired run and error analysis are needed before making a comparative research claim.
