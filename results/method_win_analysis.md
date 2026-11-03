# Method wins, losses, and ties

## Counting rule

For each task and metric, a method receives a unique win only when its score is strictly greater than both other methods. If two or three methods share the maximum score, the task is counted as a tied best. This avoids awarding the same task as a full win to multiple methods.

| Metric | BM25 unique wins | Semantic unique wins | Hybrid unique wins | Tied best | Total |
|---|---:|---:|---:|---:|---:|
| Recall@5 | 3 | 4 | 1 | 50 | 58 |
| Recall@10 | 4 | 3 | 2 | 49 | 58 |
| Reciprocal rank | 9 | 9 | 3 | 37 | 58 |

The large number of ties reflects the discreteness of file-level recall and the fact that hybrid is derived from the two individual top-10 lists. It should not be interpreted as evidence that the rankings themselves are identical.

For completeness, pairwise win/loss/tie counts are:

| Comparison | Metric | First method wins | Second method wins | Ties |
|---|---|---:|---:|---:|
| BM25 vs semantic | Recall@5 | 15 | 10 | 33 |
| BM25 vs semantic | Recall@10 | 11 | 8 | 39 |
| BM25 vs semantic | Reciprocal rank | 20 | 17 | 21 |
| BM25 vs hybrid | Recall@5 | 3 | 7 | 48 |
| BM25 vs hybrid | Recall@10 | 4 | 8 | 46 |
| BM25 vs hybrid | Reciprocal rank | 9 | 17 | 32 |
| Semantic vs hybrid | Recall@5 | 4 | 14 | 40 |
| Semantic vs hybrid | Recall@10 | 3 | 11 | 44 |
| Semantic vs hybrid | Reciprocal rank | 9 | 20 | 29 |

## 1. BM25 clearly outperformed semantic retrieval

### Task `148cbb0363427a9415265626` — etcd client configuration refactor

- **Intent:** update `epHealthCommandFunc` to reuse `clientConfigFromCmd`.
- **Anchor:** `client/v3/config.go`.
- **Anchor diff:** a large client `Config` change containing configuration field names and client terminology.
- **Gold:** `client/v3/config_test.go`; `etcdctl/ctlv3/command/ep_command.go`.
- **Metrics (BM25 / semantic / hybrid):** Recall@5 0.5 / 0.0 / 0.5; Recall@10 1.0 / 0.0 / 0.5; RR 1.0 / 0.0 / 0.5.
- **BM25 top results:** `client/v3/config_test.go`, `server/etcdmain/grpc_proxy.go`, `etcdctl/ctlv3/command/global.go`, `client/v3/client.go`, `etcdctl/ctlv3/ctl.go`; the second gold file was rank 8.
- **Semantic top results:** `CHANGELOG/CHANGELOG-3.1.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `contrib/mixin/alerts/alerts.libsonnet`, `pkg/proxy/server.go`, `etcdctl/READMEv2.md`; neither gold file appeared in the top 10.

**Observed evidence:** The query explicitly names `epHealthCommandFunc`, and that exact function occurs in gold `ep_command.go`. The other gold file shares the `client/v3/config` path with the anchor. BM25 ranked both gold files, including the paired configuration test at rank 1.

**Possible explanation:** Rare function-name and path-token matches gave BM25 precise evidence, while the semantic representation was distracted by a long configuration diff and broader repository documents. This explanation is plausible but not isolated by the current experiment.

## 2. Semantic retrieval clearly outperformed BM25

### Task `9a326250f0d9b6336a9cf026` — distributed `from_pretrained` orchestration

- **Intent:** integrate distributed configuration, tensor parallelism, FSDP, state-dict gathering, and distributed save/load.
- **Anchor:** `src/transformers/trainer.py`.
- **Anchor diff:** a long Trainer change dominated by training-loop code.
- **Gold:** `src/transformers/modeling_utils.py`.
- **Metrics (BM25 / semantic / hybrid):** Recall@5 0.0 / 1.0 / 1.0; Recall@10 0.0 / 1.0 / 1.0; RR 0.0 / 0.5 / 0.2.
- **BM25 top results:** five `examples/pytorch/.../*_no_trainer.py` training scripts occupied the first five ranks; the gold file was absent.
- **Semantic top results:** `training_args.py`, `modeling_utils.py`, a distributed FSDP trainer test, `verify_loading.py`, and `distributed/configuration_utils.py`.

**Observed evidence:** Semantic retrieval placed the gold file second and grouped it with distributed configuration and FSDP-related files. BM25 concentrated on training scripts with repeated Trainer vocabulary. The query and gold still share identifiers such as `distributed_config`, `device_mesh`, and `FSDP2`; this is not a pure no-vocabulary-overlap case.

**Possible explanation:** The embedding representation may have emphasized the overall distributed-loading operation, whereas lexical term frequency favored many training examples. A query-component ablation would be needed to separate conceptual similarity from identifier effects.

## 3. Hybrid promoted gold files from lower individual ranks

### Task `bbcbbc2c59c7bfe7fbe781a9` — Tokio framed codec readability

- **Intent:** fix whether `is_readable` reflects an empty buffer.
- **Anchor:** `tokio-util/src/codec/framed_impl.rs`.
- **Gold:** `tokio-util/tests/framed.rs`.
- **Ranks:** BM25 8, semantic 9, hybrid 4.
- **Metrics:** both individual methods had Recall@5 0.0 and Recall@10 1.0; hybrid had Recall@5 and Recall@10 of 1.0.
- **Shared high-ranked neighborhood:** all methods ranked `framed_read.rs`, `framed.rs`, and `framed_write.rs` near the top.

**Observed evidence:** The gold test appeared in both individual lists but below rank 5. RRF combined the two rank contributions and promoted it to rank 4.

**Possible explanation:** Agreement between independent rankings supplied stronger evidence than either rank alone. This is the clearest observed case where fusion improved early recall through consensus.

### Task `d6dbe66e15d389619fb51499` — etcd feature-gate migration

- **Intent:** migrate `experimental-initial-corrupt-check` to a feature gate.
- **Anchor:** `server/embed/etcd.go`.
- **Gold:** `server/etcdmain/help.go`, `server/features/etcd_features.go`, `server/embed/config_test.go`.
- **Observed ranks:** BM25 found `config_test.go` at rank 4; semantic found `etcd_features.go` at rank 1; hybrid retained them at ranks 7 and 1. Recall@10 increased from 0.333 for either individual method to 0.667 for hybrid.

**Observed evidence:** The two individual methods contributed different gold files to the fused candidate set.

**Possible explanation:** Lexical retrieval favored the anchor-adjacent test, while semantic retrieval favored the feature-gate implementation. Fusion preserved complementary signals, although it still missed `help.go`.

## 4. All methods failed

### Task `30fded9a7b09048b5c8f39de` — clap man-page environment feature

- **Intent:** put man-page environment-variable support behind the `env` feature.
- **Anchor:** `clap_mangen/src/render.rs`.
- **Anchor diff:** adds `#[cfg(feature = "env")]` around environment-option rendering.
- **Gold:** `clap_mangen/Cargo.toml`, `clap_mangen/tests/testsuite/common.rs`, `clap_mangen/tests/testsuite/roff.rs`.
- **Metrics:** all methods scored zero for Recall@5, Recall@10, and RR.
- **BM25 top results:** `help_template.rs`, `arg.rs`, `tests/builder/env.rs`, `parser.rs`, `value_parser.rs`.
- **Semantic top results:** `tests/builder/help_env.rs`, `arg.rs`, `output/help.rs`, `possible_value.rs`, `help_template.rs`.
- **Hybrid top results:** mostly the union of those general help/environment files.

**Observed evidence:** All methods retrieved files with strong `env` and help vocabulary but missed the package manifest and the two `clap_mangen` regression-test files.

**Possible explanation:** The gold changes represent packaging and downstream validation consequences rather than the most textually similar implementations. Generic `env` terminology created many plausible distractors elsewhere in the repository.

## Interpretation boundary

These examples demonstrate task-specific ranking behavior but do not isolate causal mechanisms. Exact identifiers, paths, semantic concepts, file roles, query length, repository size, and model truncation can coexist in the same task. The “possible explanation” statements are hypotheses for controlled ablations, not confirmed causes.
