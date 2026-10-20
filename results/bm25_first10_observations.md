# BM25 first-10 observations

## Scope

These are **preliminary observations from only 10 edit2ripple tasks** (six Caddy, two clap, and two Tokio tasks). They are useful for identifying cases to investigate, but they are not strong or general research conclusions.

The first-10 aggregate is mean Recall@5 **0.4500**, mean Recall@10 **0.6333**, and MRR **0.5917**. Exact ranks for every gold file are recorded in `bm25_first10_analysis.csv`.

## Task-level outcomes

| Task | Repository | Short anchor | Gold ranks in top 10 | Outcome |
|---|---|---|---|---|
| `365be40339d415a67237eee9` | caddyserver/caddy | `metrics.go` | `metrics_test.go`: 1; `routes.go`: 2 | All gold files retrieved in the top 2. |
| `7a8ae85f26f7972e3c50c14c` | caddyserver/caddy | `builtins.go` | `tlsapp.go`: 1; `options_test.go`: not retrieved | Direct implementation counterpart found; test missed. |
| `a726f272e7ddbd50bac4face` | caddyserver/caddy | `tlsapp.go` | `builtins.go`: 1; `options_test.go`: not retrieved | Direct implementation counterpart found; test missed. |
| `f0e2f6c47c53aab117eca775` | caddyserver/caddy | `formatter.go` | `parse.go`: 1; `formatter_test.go`: 8; `parse_test.go`: not retrieved | Parser implementation ranked first, but test coverage was incomplete. |
| `30fded9a7b09048b5c8f39de` | clap-rs/clap | `render.rs` | none | No gold file appeared in the top 10. |
| `8b6ab1ba0883ff8104d28524` | clap-rs/clap | `parser.rs` | `arg.rs`: 2; `default_vals.rs`: 9 | Both gold files retrieved, but the test was relatively late. |
| `88f4b3f165035260aec813d3` | caddyserver/caddy | `listeners.go` | none | The only gold file, `listeners_test.go`, was not in the top 10. |
| `0631449332f969f725276ef8` | caddyserver/caddy | `parse.go` | `parse_test.go`: 6 | Gold retrieved outside the top 5. |
| `a4bb43c519262529c3cd0ddf` | tokio-rs/tokio | `open.rs` | `write.rs`: 1; `fs/write.rs`: 2; `op.rs`: 3 | All gold implementation files retrieved in the top 3. |
| `18a155cebfee9969b166934c` | tokio-rs/tokio | `context.rs` | `worker.rs`: 4; `scheduler/mod.rs`: 5; `runtime/mod.rs`: not retrieved | Two of three runtime/scheduler files retrieved in the top 5. |

## Preliminary patterns

### Where BM25 performed well

- The two complete-recall cases had substantial shared code vocabulary. The metrics task repeats terms such as `metrics`, `route`, `handler`, and `instrumentation`; its gold files ranked 1 and 2. The Tokio io-uring task repeats distinctive identifiers and terms including `Completable`, `Cancellable`, `complete`, `operation`, `runtime`, and `uring`; all three gold files ranked in the top 3.
- Direct implementation counterparts often ranked highly. `tlsapp.go` and `builtins.go` each ranked first when the other was the anchor, `parse.go` ranked first for the formatter change, and `arg.rs` ranked second for the `default_values` change.
- Exact or near-exact path and identifier terminology appears helpful in these examples. Terms such as `metrics`, `httpcaddyfile`, `caddyfile`, `formatter`, `default`, `runtime`, `scheduler`, and `uring` occur in the query/diff and in relevant paths or code. Distinctive function/type names such as `Completable`, `Cancellable`, and `default_values` also coincide with strong rankings.

### Where BM25 struggled

- The clap man-page feature-gating task retrieved no gold files. Its short query emphasizes generic terms such as `env`, `feature`, and `support`; one gold target is `Cargo.toml`, whose role is configuration rather than an implementation with the same lexical form. Other files containing those common terms displaced the gold package/test files.
- The ECH/QUIC listener task also retrieved no gold file. Although `listeners_test.go` shares the filename stem `listeners`, much of the query's highly specific terminology (`ECH`, QUIC, TLS configuration, encrypted client hello keys) occurs across many TLS/HTTP implementation files, all of which occupied the top 10. Filename proximity alone was not enough.
- Some gold files were only found late: `parse_test.go` at rank 6, `formatter_test.go` at rank 8, and `default_vals.rs` at rank 9. This suggests that lexical evidence can identify the right neighborhood while still ranking several related files ahead of the labelled ripple file.
- Conceptually related files with different surface terminology appear harder in these cases. `Cargo.toml` in the feature-gating task and `runtime/mod.rs` in the worker-index task express packaging or public-API consequences that are related to the change but do not necessarily repeat the most distinctive changed identifiers. This is a hypothesis for later testing, not a conclusion from ten tasks.

### Test files versus implementation files

- Behavior is mixed rather than uniformly better for either category. `metrics_test.go` ranked first, but `options_test.go` was missed in two paired tasks, `parse_test.go` ranged from rank 6 to not retrieved, `formatter_test.go` ranked 8, `default_vals.rs` ranked 9, and the test-only listener target was missed.
- In this small sample, directly coupled implementation files more often occupied the very top ranks, especially when changed identifiers appeared in their contents. Test files were competitive when their path/content repeated the query vocabulary, but several were pushed toward or beyond rank 10.
- The sample mixes languages, repositories, gold-set sizes, and change types, so a larger category-controlled analysis is needed before attributing a systematic difference to test versus implementation files.

## Follow-up questions suggested by these cases

- Measure identifier/path-token overlap against rank across all 58 tasks instead of judging overlap manually.
- Label gold files by rough role (test, implementation, configuration/documentation) and compare within repositories where sample sizes permit.
- Check whether semantic retrieval improves the low-overlap configuration/public-API cases while retaining the strong exact-identifier cases found by BM25.
