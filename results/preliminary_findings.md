# Preliminary findings: repository context retrieval

> These findings describe the 58 tasks in Agent Retrieval Bench `v2_edit2ripple`. They are preliminary and should not be presented as universal conclusions about repository retrieval.

## Experiment Setup

- **Dataset:** 58 `v2_edit2ripple` tasks, each matched to its exact `repo + base_commit` corpus snapshot.
- **Retrieval unit:** corpus chunks scored first, then deduplicated to unique file paths using each file's highest-scoring chunk. The supplied anchor file is excluded.
- **Query:** `query.intent + query.anchor_diff` for every method.
- **Document:** `path + symbol + chunk text` for BM25 and semantic retrieval.
- **BM25:** `rank-bm25` with camelCase/snake_case-aware tokenization.
- **Semantic:** normalized embeddings from `sentence-transformers/all-MiniLM-L6-v2` on CPU, ranked by cosine similarity. The model's standard 256-token maximum sequence length applies.
- **Hybrid:** file-level Reciprocal Rank Fusion over the BM25 and semantic top-10 lists, using the untuned conventional constant `k=60`; absent files contribute zero.
- **Metrics:** file-level Recall@5, Recall@10, and reciprocal rank, averaged over tasks.

## Results

| Method | Recall@5 | Recall@10 | MRR |
|---|---:|---:|---:|
| BM25 | 0.3980 | 0.5158 | 0.4197 |
| Semantic | 0.3420 | 0.5086 | 0.3278 |
| Hybrid RRF | **0.4555** | **0.5761** | **0.4706** |

The full semantic run took 4,158.6 seconds (69.3 minutes) on CPU while encoding 44 unique snapshots. Hybrid fusion itself took about 0.003 seconds from saved rankings; that number excludes the cost of producing its BM25 and semantic inputs and therefore is not an end-to-end latency comparison. The earlier BM25 run did not record elapsed time.

## Preliminary Observations

1. **Hybrid has the strongest aggregate metrics in this run.** Relative to BM25, hybrid improves mean Recall@5 by 0.0575, Recall@10 by 0.0603, and MRR by 0.0509. This is an observed result for this subset, not evidence that RRF will always dominate.
2. **BM25 remains stronger than the semantic baseline overall.** BM25 exceeds semantic retrieval by 0.0560 Recall@5 and 0.0919 MRR; Recall@10 is much closer (difference 0.0072). The task-level BM25/semantic comparison has 20 BM25 wins, 18 semantic wins, and 20 ties or mixed trade-offs under a majority-of-three-metrics rule, showing considerable task variation behind the means.
3. **Increasing depth from 5 to 10 materially improves recall.** Recall rises by 0.1178 for BM25, 0.1667 for semantic retrieval, and 0.1207 for hybrid. Semantic retrieval's relatively large increase suggests that it often identifies relevant files but ranks them outside the first five.
4. **Fusion sometimes promotes complementary evidence, but it is not an oracle.** For Tokio task `bbcbbc2c59c7bfe7fbe781a9`, the gold test file was BM25 rank 8 and semantic rank 9; agreement promoted it to hybrid rank 4. For tasks `d6dbe66e15d389619fb51499` and `fa3cd07539adf20ceb766dda`, BM25 and semantic retrieved different gold files and hybrid doubled Recall@10 from 0.333 to 0.667. However, hybrid was below the better individual method on seven tasks for Recall@5 and seven for Recall@10.
5. **Lexical and semantic strengths are not explained by one signal.** Exact identifier overlap helped BM25 in the etcd `epHealthCommandFunc` task, while semantic retrieval found `.golangci.yml` for an HTTP/3 change despite no meaningful query/path token overlap. Other semantic wins still contained exact identifiers, so “lexical versus conceptual” is not a clean binary distinction.
6. **Test-file behavior is mixed.** Among 45 test gold labels, BM25 hit 0.400 at five and 0.556 at ten; semantic retrieval hit 0.289 and 0.422. Among 54 non-test labels, the corresponding rates were 0.389/0.463 for BM25 and 0.370/0.481 for semantic retrieval. These descriptive per-file rates are confounded by repository and task type.

## Failure Cases

Fourteen tasks had zero Recall@10 for all three methods. Representative cases include:

- `30fded9a7b09048b5c8f39de` (`clap_mangen/src/render.rs`): all methods missed `Cargo.toml` and two man-page tests for an environment-feature gating change. Configuration and downstream test consequences were not recovered.
- `88f4b3f165035260aec813d3` (`listeners.go`): all methods missed `listeners_test.go` for the ECH/QUIC listener change, despite the paired filename.
- `78906550756a325d653e88b9` (Spring Boot `WebFluxProperties.java`): all methods missed both `HttpHandlerAutoConfiguration.java` and its test.
- `eb415665c7189dd5c704b2dd` / `8360be1c075445a4b64aa109` (Transformers): reciprocal changes between `conversion_mapping.py` and `finegrained_fp8.py` were missed in both directions.
- `99089b7d090ba9567c42f198` and `bf0ff8578398a3db3e0fcad4` (Vite): all methods missed `packages/vite/package.json` as the relevant configuration file for plugin changes.

Because hybrid only fuses the union of the two input top-10 lists, it cannot recover a gold file absent from both lists.

## Questions Raised

- Would fusing deeper input lists (for example top 25 or top 50) recover useful complementary candidates without unacceptable latency or noise?
- How much of each method's behavior comes from query intent versus anchor diff, and from path/symbol fields versus chunk text?
- Does semantic truncation at 256 tokens disproportionately affect long diffs or long code chunks?
- Are differences by test/configuration/implementation role stable after controlling for repository and language?
- Are the aggregate improvements robust under paired bootstrap confidence intervals or another task-level uncertainty analysis?
- What are indexing cost, warm-query latency, memory, and storage costs for each strategy under the same hardware conditions?

## Logical Next Experiment

Use a predeclared development split—not the full 58-task evaluation set—to compare RRF candidate depths (top 10, 25, and 50) while keeping `k=60`, the model, queries, and labels fixed. Record end-to-end indexing/query time and memory, select the depth on the development split, and evaluate it once on the held-out tasks. This directly tests whether the current top-10 fusion ceiling explains the remaining misses without tuning against the full benchmark.
