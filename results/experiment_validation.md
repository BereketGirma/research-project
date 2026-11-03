# Retrieval experiment validation

## Scope

The audit compared the three saved all-task result files against the 58 records in Agent Retrieval Bench `v2_edit2ripple` and recomputed every metric from the stored file rankings. The benchmark and corpus are currently available in the sibling checkout `../agent-retrieval-bench/data/`; the project runners resolve that location explicitly.

| Check | BM25 | Semantic | Hybrid |
|---|---|---|---|
| 58 tasks evaluated | Pass: 58 unique IDs | Pass: 58 unique IDs | Pass: 58 unique IDs |
| Same queries | Pass: `intent + anchor_diff` via shared `build_query` | Pass: same shared `build_query` | Pass: fuses rankings produced from the same queries |
| Same corpus snapshots | Pass: exact `repo + base_commit` | Pass: exact `repo + base_commit` | Pass: aligned BM25/semantic rows are required before fusion |
| Anchor excluded | Pass: absent from all 58 top-10 lists | Pass: absent from all 58 top-10 lists | Pass: absent from all 58 top-10 lists |
| File-level deduplication | Pass: 10 unique file paths per task | Pass: 10 unique file paths per task | Pass: 10 unique file paths per task |
| Recall@5 | Pass: recomputed mean 0.3980 | Pass: recomputed mean 0.3420 | Pass: recomputed mean 0.4555 |
| Recall@10 | Pass: recomputed mean 0.5158 | Pass: recomputed mean 0.5086 | Pass: recomputed mean 0.5761 |
| MRR | Pass: recomputed mean 0.4197 | Pass: recomputed mean 0.3278 | Pass: recomputed mean 0.4706 |

## Detailed checks

- The three CSV files contain the same task IDs in benchmark order, with identical repositories, base commits, anchor files, and gold-file lists.
- Every `repo + base_commit` pair resolves to an existing corpus snapshot. No benchmark task is missing or duplicated.
- Each saved top-10 list contains exactly 10 distinct file paths. Across 174 task-method rankings, no anchor file is present.
- Recall@5, Recall@10, and reciprocal rank were recomputed from each row's gold files and top-10 list. All 522 per-task metric triples match their stored values exactly within floating-point tolerance.
- All three summaries match means recomputed from their respective 58 rows.
- BM25 and semantic retrieval both score chunks built from `path + symbol + text`, retain the highest-scoring chunk per file, and use the same file-level evaluator. Hybrid RRF combines the already deduplicated BM25 and semantic file rankings with fixed `k=60` and input depth 10.
- The semantic model recorded in every semantic row is `sentence-transformers/all-MiniLM-L6-v2`; no model switch occurred.

## Outcome

No inconsistency requiring a rerun was found. Existing experiment outputs were preserved and used as immutable inputs to the final analysis.
