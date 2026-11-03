# Retrieval failure analysis

## Selection

The ten tasks below were selected from the fourteen tasks where BM25, semantic, and hybrid retrieval all had Recall@10 = 0. They therefore represent complete top-10 failures rather than small rank differences. Top results show the first three files for compactness.

## 1. `30fded9a7b09048b5c8f39de` — clap-rs/clap

- **Anchor:** `clap_mangen/src/render.rs`
- **Intent:** place man-page environment support behind the `env` feature.
- **Gold:** `clap_mangen/Cargo.toml`; `clap_mangen/tests/testsuite/common.rs`; `clap_mangen/tests/testsuite/roff.rs`.
- **BM25 top:** `clap_builder/src/output/help_template.rs`; `clap_builder/src/builder/arg.rs`; `tests/builder/env.rs`.
- **Semantic top:** `tests/builder/help_env.rs`; `clap_builder/src/builder/arg.rs`; `clap_builder/src/output/help.rs`.
- **Hybrid top:** `clap_builder/src/builder/arg.rs`; `help_template.rs`; `tests/builder/env.rs`.
- **Possible explanation:** common `env` and help vocabulary favored general builder files, while the gold set contains a package manifest and downstream `clap_mangen` tests.

## 2. `88f4b3f165035260aec813d3` — caddyserver/caddy

- **Anchor:** `listeners.go`
- **Intent:** propagate ECH keys to the QUIC listener.
- **Gold:** `listeners_test.go`.
- **BM25 top:** `modules/caddytls/connpolicy.go`; `modules/caddytls/ech.go`; `modules/caddyhttp/server.go`.
- **Semantic top:** `modules/caddyhttp/server.go`; a TLS Caddyfile integration test; `modules/caddytls/capools.go`.
- **Hybrid top:** `server.go`; `ech.go`; `reverseproxy/httptransport.go`.
- **Possible explanation:** ECH/QUIC/TLS vocabulary strongly matched implementation files throughout the repository, while the paired root-level regression test did not contain enough distinctive evidence to enter the top 10.

## 3. `78906550756a325d653e88b9` — spring-projects/spring-boot

- **Anchor:** `.../webflux/autoconfigure/WebFluxProperties.java`
- **Intent:** expose an application-wide `spring.webflux.default-html-escape` property.
- **Gold:** `HttpHandlerAutoConfiguration.java`; `HttpHandlerAutoConfigurationTests.java`.
- **BM25 top:** `DateTimeFormatters.java`; Web MVC `WebMvcProperties.java`; `WebConversionService.java`.
- **Semantic top:** a WebFlux error-handler integration test; Gson auto-configuration tests; validation integration tests.
- **Hybrid top:** `DateTimeFormatters.java`; the WebFlux error-handler test; Gson auto-configuration tests.
- **Possible explanation:** the change crosses from a configuration-property class into handler auto-configuration. Similar Web MVC/property and auto-configuration files created strong distractors in a large repository.

## 4. `33c925493a0fbff71d6badc9` — clap-rs/clap

- **Anchor:** `clap_builder/src/error/format.rs`
- **Intent:** quote empty default values in help output.
- **Gold:** `clap_builder/src/util/mod.rs`.
- **BM25 top:** `error/mod.rs`; `output/usage.rs`; `builder/styled_str.rs`.
- **Semantic top:** `error/mod.rs`; `tests/builder/empty_values.rs`; `tests/examples.rs`.
- **Hybrid top:** `error/mod.rs`; `output/usage.rs`; `tests/builder/empty_values.rs`.
- **Possible explanation:** the gold logic resides in a generically named utility module, while query vocabulary points more directly to formatting, errors, help output, and empty-value tests.

## 5. `269e3e34c64f7e5d74b5fefd` — clap-rs/clap

- **Anchor:** `clap_builder/src/output/help_template.rs`
- **Intent:** the same empty-default-value quoting change as task 4.
- **Gold:** `clap_builder/src/util/mod.rs`.
- **BM25 top:** `output/help.rs`; `output/mod.rs`; `output/usage.rs`.
- **Semantic top:** `src/_features.rs`; `tests/builder/help.rs`; `tests/derive/default_value.rs`.
- **Hybrid top:** `builder/command.rs`; `builder/arg.rs`; `output/help.rs`.
- **Possible explanation:** direct help/default-value neighbors overwhelmed a distant generic utility file. The repeated failure from two anchors supports an indirect helper relationship rather than a single-anchor anomaly.

## 6. `eb415665c7189dd5c704b2dd` — huggingface/transformers

- **Anchor:** `src/transformers/conversion_mapping.py`
- **Intent:** fix configuration reading, kernel error handling, and missing expert conversion.
- **Gold:** `src/transformers/integrations/finegrained_fp8.py`.
- **BM25 top:** `fusion_mapping.py`; weight-converter documentation; `integrations/peft.py`.
- **Semantic top:** Qwen Omni configuration and modular files; `.github/workflows/anti-slop.yml`.
- **Hybrid top:** `fusion_mapping.py`; Qwen Omni configuration; weight-converter documentation.
- **Possible explanation:** the intent is broad and uses common configuration/conversion vocabulary, while the gold relationship crosses from a generic conversion registry to a specific FP8 integration.

## 7. `8360be1c075445a4b64aa109` — huggingface/transformers

- **Anchor:** `src/transformers/integrations/finegrained_fp8.py`
- **Intent:** the reciprocal side of the configuration/kernel conversion change.
- **Gold:** `src/transformers/conversion_mapping.py`.
- **BM25 top:** an FP8 quantizer; core-model-loading tests; `integrations/hub_kernels.py`.
- **Semantic top:** Qwen Omni configuration and modular files; `.github/workflows/anti-slop.yml`.
- **Hybrid top:** Qwen configuration; an FP8 quantizer; Qwen modular code.
- **Possible explanation:** local FP8 and kernel neighbors looked more relevant than the repository-wide mapping file. Failure in both anchor directions supports a cross-module registration relationship that neither method represented well.

## 8. `262ecc80fa3618111feb4987` — huggingface/transformers

- **Anchor:** `src/transformers/cli/serving/model_manager.py`
- **Intent:** add multimodal audio/video support to serving APIs.
- **Gold:** `src/transformers/cli/serving/chat_completion.py`.
- **BM25 top:** `serving/transcription.py`; `serving/utils.py`; `dynamic_module_utils.py`.
- **Semantic top:** Qwen Omni and vision-language model tests.
- **Hybrid top:** `transcription.py`; a Qwen Omni processing test; `serving/utils.py`.
- **Possible explanation:** lexical retrieval emphasized adjacent audio-serving utilities, while semantic retrieval emphasized multimodal model families. The gold chat-completion handler was one of several plausible serving surfaces in a broad change.

## 9. `99089b7d090ba9567c42f198` — vitejs/vite

- **Anchor:** `packages/vite/src/node/plugins/index.ts`
- **Intent:** always use the ESM Oxc runtime.
- **Gold:** `packages/vite/package.json`.
- **BM25 top:** `node/config.ts`; `plugins/html.ts`; `modulePreloadPolyfill.ts`.
- **Semantic top:** plugin-legacy changelog; `dynamicImportVars.ts`; a module-preload test.
- **Hybrid top:** `node/config.ts`; plugin-legacy changelog; `dynamicImportVars.ts`.
- **Possible explanation:** the required package/dependency metadata update is structurally related to runtime selection but contains little code-level vocabulary from the plugin change.

## 10. `bf0ff8578398a3db3e0fcad4` — vitejs/vite

- **Anchor:** `packages/vite/src/node/plugins/oxc.ts`
- **Intent:** the same ESM Oxc runtime change as task 9.
- **Gold:** `packages/vite/package.json`.
- **BM25 top:** migration documentation; `plugins/esbuild.ts`; optimizer scanning code.
- **Semantic top:** `plugins/importAnalysis.ts`; `node/build.ts`; `node/config.ts`.
- **Hybrid top:** migration documentation; the Oxc plugin test; import-analysis code.
- **Possible explanation:** both methods stayed within implementation and documentation neighborhoods and failed to infer the package-manifest consequence. Repetition across two anchors strengthens the configuration-file failure pattern.

## Recurring failure categories

1. **Configuration or manifest consequences:** `Cargo.toml` and `package.json` changes were missed when the query primarily described runtime code behavior (tasks 1, 9, and 10).
2. **Indirect helper or registration relationships:** generically named utility/mapping files were difficult to connect to specific formatting or integration changes (tasks 4–7).
3. **Cross-module architectural propagation:** property-to-auto-configuration and registry-to-integration relationships crossed module boundaries without a strong direct textual link (tasks 3, 6, and 7).
4. **Broad vocabulary with many plausible neighbors:** ECH/TLS, multimodal serving, configuration, and help/environment terminology produced numerous relevant-looking distractors (tasks 1, 2, 6, and 8).
5. **Test-file selection among implementation-heavy matches:** the Caddy listener regression test was missed despite a paired name, and several methods preferred implementation files with richer domain terminology (task 2).

These categories summarize observed examples in this benchmark. They are not mutually exclusive, and the proposed reasons remain hypotheses until tested with targeted query/document ablations or dependency-aware retrieval signals.
