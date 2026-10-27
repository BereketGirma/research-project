# BM25 versus semantic retrieval: all edit2ripple tasks

> These are controlled results for the 58-task subset. Explanations below separate measured outcomes from hypotheses that require additional analysis.

## Overall results

| Method | Mean Recall@5 | Mean Recall@10 | MRR |
|---|---:|---:|---:|
| BM25 | 0.3980 | 0.5158 | 0.4197 |
| Semantic | 0.3420 | 0.5086 | 0.3278 |

A task-level outcome is assigned by which method wins more of Recall@5, Recall@10, and reciprocal rank; equal win counts are reported as tie/mixed.

- BM25 task wins: **20**
- Semantic task wins: **18**
- Ties or mixed trade-offs: **20**

## Largest clear differences

The examples below are selected mechanically: the named method is no worse on any metric and has the largest summed advantage across the three metrics.

### BM25 clear wins

- `85fc8542cd9f38c6414a851e` (huggingface/transformers, `src/transformers/models/umt5/configuration_umt5.py`): R@5 1.000/0.000, R@10 1.000/0.000, RR 1.000/0.000 (BM25/semantic).
- `148cbb0363427a9415265626` (etcd-io/etcd, `client/v3/config.go`): R@5 0.500/0.000, R@10 1.000/0.000, RR 1.000/0.000 (BM25/semantic).
- `4f6c4f2d9b8ae3a553dfbf1f` (gin-gonic/gin, `binding/form_mapping.go`): R@5 1.000/0.000, R@10 1.000/0.000, RR 0.500/0.000 (BM25/semantic).
- `0150e5de390fa7c521175b89` (gin-gonic/gin, `binding/form_mapping.go`): R@5 1.000/0.000, R@10 1.000/0.000, RR 0.333/0.000 (BM25/semantic).
- `157caed0d859c12fb0ea4caf` (gin-gonic/gin, `context.go`): R@5 1.000/0.000, R@10 1.000/0.500, RR 1.000/0.167 (BM25/semantic).

### semantic clear wins

- `9a326250f0d9b6336a9cf026` (huggingface/transformers, `src/transformers/trainer.py`): R@5 0.000/1.000, R@10 0.000/1.000, RR 0.000/0.500 (BM25/semantic).
- `b09afd5adcd28d23a8142452` (etcd-io/etcd, `cache/ringbuffer.go`): R@5 0.000/1.000, R@10 0.000/1.000, RR 0.000/0.250 (BM25/semantic).
- `02faf838effb2bcebf8d8cca` (gin-gonic/gin, `render/data.go`): R@5 0.000/1.000, R@10 0.000/1.000, RR 0.000/0.200 (BM25/semantic).
- `cbb729b2af79ab394110ba8e` (gin-gonic/gin, `context.go`): R@5 0.000/1.000, R@10 1.000/1.000, RR 0.143/1.000 (BM25/semantic).
- `bb9cf609f8e5521ab080803e` (gin-gonic/gin, `gin.go`): R@5 0.000/0.500, R@10 0.000/1.000, RR 0.000/0.250 (BM25/semantic).

## Observed task evidence

- In task `148cbb0363427a9415265626`, the query names `epHealthCommandFunc`; that exact function name occurs in gold `etcdctl/ctlv3/command/ep_command.go`. BM25 retrieved the two gold files at ranks 8 and 1, while semantic retrieval retrieved neither. This is direct evidence of a lexical/identifier-friendly case.
- In task `4f6c4f2d9b8ae3a553dfbf1f`, anchor `binding/form_mapping.go`, gold `binding/form_mapping_test.go`, and the query share `binding`/`form` terminology. BM25 ranked the test file second; semantic retrieval missed it. The paired filename and path terminology are observed, although they cannot alone prove why the score differed.
- In task `9a326250f0d9b6336a9cf026`, a long query about distributed `from_pretrained` orchestration points to `modeling_utils.py`. Semantic retrieval ranked it second and BM25 missed it. The query and target share identifiers including `distributed_config`, `device_mesh`, and `FSDP2`, so this is not a pure “different terminology” example; the broader orchestration context and long, noisy query are plausible contributors that require a targeted ablation.
- In task `bb9cf609f8e5521ab080803e`, the HTTP/3 change retrieved `.golangci.yml` at semantic rank 4 even though the gold path shares no meaningful token with the query; BM25 missed it. This is consistent with semantic retrieval connecting a build/tooling consequence to the feature description, but content-level causal attribution remains a hypothesis.
- In task `cbb729b2af79ab394110ba8e`, semantic retrieval ranked `context_test.go` first for a protocol-buffer content-negotiation change, while BM25 ranked it seventh. Both the paired filename and conceptual content are present, so the result does not isolate which signal drove the improvement.

## Test versus non-test gold files

Across the 99 individual gold-file labels, 45 were classified as test files using path/name conventions. Their observed file hit rates were:

| Method | Test hit@5 | Test hit@10 | Non-test hit@5 | Non-test hit@10 |
|---|---:|---:|---:|---:|
| BM25 | 0.400 | 0.556 | 0.389 | 0.463 |
| Semantic | 0.289 | 0.422 | 0.370 | 0.481 |

In this subset, BM25 did not show a general disadvantage on test files, while semantic retrieval's test-file hit rates were lower than its non-test hit rates. These are per-gold-file descriptive rates, not task-level metrics, and file role is confounded with repository, language, and change type.

## Interpretation boundaries

The CSV records observed per-task metrics and winners. Exact identifiers, path terminology, conceptual similarity, and test-versus-implementation roles can coexist in one task, so the examples do not isolate causal effects. Repository and language are also confounded with task type in this subset. Controlled query-component and document-component ablations would be needed to attribute performance differences to a specific signal.
