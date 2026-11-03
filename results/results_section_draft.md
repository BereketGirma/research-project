# Results

## Experimental Setup

The retrieval experiment used the `v2_edit2ripple` subset of Agent Retrieval Bench, containing 58 repository-level change tasks. Each task specifies a repository, base commit, known anchor file, natural-language intent, anchor diff, and one or more gold ripple files. The corpus was matched using the exact repository and base commit. Although corpus entries are code chunks, evaluation was performed at file level: chunks were ranked and then deduplicated by retaining the highest-scoring chunk for each file. The known anchor file was excluded from all candidate rankings.

Three retrieval approaches were compared while holding the benchmark tasks, query, corpus snapshot, document fields, ranking depth, and evaluation code constant. BM25 used lexical scoring over `path + symbol + chunk text` with tokenization that separates camelCase and snake_case. Semantic retrieval encoded the same document representation and the shared `intent + anchor_diff` query with `sentence-transformers/all-MiniLM-L6-v2`; normalized embeddings were ranked using cosine similarity. The hybrid method applied Reciprocal Rank Fusion (RRF) to the deduplicated BM25 and semantic top-10 file lists using a fixed, untuned constant of `k=60`.

Retrieval quality was measured using file-level Recall@5, Recall@10, and reciprocal rank. Recall@K measures the fraction of gold files found in the first K results, while reciprocal rank measures how early the first gold file appears. All three methods were evaluated on the same ordered set of 58 tasks; no tasks were skipped.

## Overall Results

| Method | Mean Recall@5 | Mean Recall@10 | MRR |
|---|---:|---:|---:|
| BM25 | 0.3980 | 0.5158 | 0.4197 |
| Semantic | 0.3420 | 0.5086 | 0.3278 |
| Hybrid RRF | **0.4555** | **0.5761** | **0.4706** |

Hybrid RRF obtained the highest mean value for all three metrics. Relative to BM25, hybrid improved mean Recall@5 by 0.0575, Recall@10 by 0.0603, and MRR by 0.0509. BM25 exceeded the semantic baseline by 0.0560 Recall@5 and 0.0919 MRR, while their Recall@10 values were closer, differing by 0.0072.

Moving from K=5 to K=10 increased recall for every method: by 0.1178 for BM25, 0.1667 for semantic retrieval, and 0.1207 for hybrid retrieval. The larger increase for semantic retrieval suggests that it often located relevant files outside the first five positions. This interpretation is limited to the current model and benchmark; it does not establish a general property of semantic retrieval.

The recorded semantic run took approximately 4,158.6 seconds (69.3 minutes) on CPU while encoding 44 unique corpus snapshots. RRF fusion took approximately 0.003 seconds from already generated rankings, but this excludes the cost of producing both input rankings and is therefore not an end-to-end hybrid latency. The earlier BM25 run did not record elapsed time, so a controlled runtime comparison cannot yet be made.

## Comparison of Retrieval Approaches

Unique wins were counted only when one method strictly exceeded both other methods for a task and metric. A shared maximum was counted as a tie.

| Metric | BM25 wins | Semantic wins | Hybrid wins | Tied best |
|---|---:|---:|---:|---:|
| Recall@5 | 3 | 4 | 1 | 50 |
| Recall@10 | 4 | 3 | 2 | 49 |
| Reciprocal rank | 9 | 9 | 3 | 37 |

The high number of tied-best outcomes reflects the discreteness of file-level recall and the dependence of hybrid retrieval on the two individual rankings. It does not imply that the ordered file lists were identical. Task-level inspection showed that lexical and semantic methods could produce meaningfully different rankings even when their final metric values tied.

Paired two-sided Wilcoxon signed-rank tests were applied to all method pairs and metrics. The tests excluded zero differences and used asymptotic p-values because of the many ties. BM25 versus semantic retrieval was not statistically significant for Recall@5 (`p=0.4811`), Recall@10 (`p=0.9673`), or reciprocal rank (`p=0.1473`). BM25 versus hybrid was also non-significant for Recall@5 (`p=0.2439`), Recall@10 (`p=0.1914`), and reciprocal rank (`p=0.1621`). Semantic versus hybrid was significant for Recall@5 before multiple-comparison correction (`p=0.0465`) but not after Holm correction (`p_Holm=0.3723`). The semantic-versus-hybrid reciprocal-rank difference remained significant after Holm correction (`W=85.0`, `p=0.0041`, `p_Holm=0.0373`). Semantic versus hybrid Recall@10 was not significant (`p=0.1298`).

These tests do not show a statistically reliable hybrid advantage over BM25 in this 58-task sample, despite the higher hybrid means. They do provide evidence of a systematic hybrid advantage over semantic retrieval for reciprocal rank under the chosen test. Non-significant results should not be interpreted as proof of equivalence, particularly because only 10–37 task pairs had nonzero differences depending on the comparison.

## Task-Level Analysis

Several tasks illustrate why aggregate means alone are insufficient. In etcd task `148cbb0363427a9415265626`, the query explicitly named `epHealthCommandFunc`, and the gold implementation contained that identifier. BM25 ranked the two gold files at positions 1 and 8, whereas semantic retrieval missed both. This is observed evidence of a task with strong identifier and path signals. A possible explanation is that rare lexical matches were more discriminative than the embedding representation for the long configuration diff.

Conversely, in Transformers task `9a326250f0d9b6336a9cf026`, semantic retrieval ranked the gold `modeling_utils.py` file second for a distributed `from_pretrained` orchestration change, while BM25 retrieved several training-example files and missed the gold target. The semantic ranking grouped the gold file with distributed configuration and FSDP-related files. However, the query and target also shared identifiers such as `distributed_config` and `device_mesh`; the example therefore does not isolate semantic similarity from lexical evidence.

Hybrid retrieval sometimes benefited from agreement between lower individual ranks. In Tokio task `bbcbbc2c59c7bfe7fbe781a9`, the gold test file appeared at BM25 rank 8 and semantic rank 9. RRF promoted it to rank 4, raising Recall@5 from 0 to 1. In etcd task `d6dbe66e15d389619fb51499`, BM25 and semantic retrieval found different gold files; hybrid retained both and increased Recall@10 from 0.333 for either individual method to 0.667. These examples show complementary fusion behavior. However, hybrid was below the better individual method on seven tasks for Recall@5 and seven tasks for Recall@10, so fusion did not uniformly preserve the best input ranking.

Descriptive analysis of individual gold labels also found mixed file-role behavior. Among 45 test-file gold labels, BM25 hit rates were 0.400 at five and 0.556 at ten, compared with 0.289 and 0.422 for semantic retrieval. Among 54 non-test labels, BM25 achieved 0.389/0.463 and semantic retrieval achieved 0.370/0.481. These rates are confounded with repository, language, and task type and should not be interpreted as an isolated test-versus-implementation effect.

## Failure Analysis

Fourteen tasks had Recall@10 of zero for all three methods. Several recurring patterns appeared in ten inspected cases. First, configuration and manifest consequences were difficult to retrieve: both Vite Oxc tasks missed `package.json`, and the clap man-page feature task missed `Cargo.toml`. Second, indirect helper and registration relationships caused failures, including changes whose gold target was a generic `util/mod.rs` or a repository-wide conversion mapping. Third, cross-module propagation was challenging, as seen in the Spring Boot property-to-auto-configuration task and the reciprocal Transformers conversion/FP8 tasks. Fourth, broad domain terminology such as ECH/TLS, multimodal serving, configuration, and help/environment produced many plausible distractors. Finally, test-file targets could be displaced by richer implementation matches, as occurred for the Caddy listener regression test.

These categories are supported by repeated examples, but they overlap. For instance, a package manifest is both a configuration file and a cross-module consequence. The analysis therefore identifies hypotheses about retrieval difficulty rather than mutually exclusive causal classes.

## Statistical Analysis

The Wilcoxon analysis used all 58 paired task observations but excluded task pairs with exactly equal scores, as required by the selected zero-difference method. Effective nonzero sample sizes ranged from 10 to 37. Metric distributions were discrete and contained many ties, so asymptotic rather than exact p-values were used. Holm correction was reported across all nine method-metric tests.

Only the semantic-versus-hybrid reciprocal-rank comparison remained significant after correction. The higher hybrid aggregate means for Recall@5 and Recall@10 were not accompanied by corrected significance in this sample. These findings suggest that hybrid retrieval most consistently improved the position of the first relevant file relative to the semantic baseline, while evidence for broader recall improvements is less conclusive at the current sample size.

## Preliminary Interpretation

The results suggest that lexical and semantic retrieval exploit partly complementary signals in this benchmark. BM25 performed strongly when rare identifiers, filenames, or direct path terminology were discriminative. Semantic retrieval produced clear wins on some broader repository operations, but it also underperformed BM25 on the aggregate metrics and incurred substantially greater unindexed CPU cost. Hybrid RRF achieved the strongest aggregate results and reduced the number of complete Recall@10 failures from 21 for BM25 and 23 for semantic retrieval to 16. Its advantage appears to arise from both consensus promotion and preservation of different gold files supplied by the individual rankings.

At the same time, the statistical results and failure cases argue against claiming that hybrid retrieval is universally superior. The benchmark contains only 58 tasks, many per-task metric values tie, and hybrid is limited to the union of two top-10 lists. In this benchmark, the evidence supports hybrid retrieval as a promising combination strategy, particularly for ranking the first relevant file, while leaving open questions about candidate depth, runtime cost, query truncation, and dependency-aware retrieval.
