# Small repository-QA extension plan

## Research question

Does changing only the repository retrieval strategy—BM25, semantic, or hybrid RRF—change an LLM's ability to explain a repository-level change accurately and with evidence from the retrieved code?

This is a downstream extension of the validated retrieval experiment. It should remain small and should not be used to tune the retrieval methods against the 58-task evaluation set.

## Proposed pilot sample

Use **8 tasks** selected before running the LLM:

- 2 tasks where BM25 clearly outperformed semantic retrieval;
- 2 tasks where semantic retrieval clearly outperformed BM25;
- 2 tasks where hybrid promoted complementary gold evidence;
- 2 tasks where all methods failed at Recall@10.

The categories should be based on the existing validated results. Within each category, choose tasks spanning different repositories where possible. This purposive pilot is suitable for mechanism exploration, not population-level performance estimates. A later confirmatory study would require a preregistered or randomized sample.

## Question format

For each task, derive one repository-understanding question from `query.intent` and `query.anchor_diff` without exposing `gold.files`. A consistent template could be:

> Given the requested change and the anchor-file diff, explain which additional repository components are likely affected, what behavior must remain consistent, and what tests or configuration updates are needed. Cite the supplied repository files in the answer.

The same task question must be used for all three retrieval conditions.

## Context construction

For each retrieval method:

1. Include the task intent and anchor diff.
2. Include the known anchor file or the changed anchor chunks under a fixed token allowance.
3. Add retrieved context from the method's top-ranked files in rank order.
4. Use the same maximum number of files and the same total context-token budget for every method.
5. For each retrieved file, include the highest-ranked chunk first and add further chunks only under a deterministic rule shared across methods.
6. Label every context block with its repository path and line range so the model can cite evidence.
7. Truncate using the same deterministic policy when the context budget is exceeded.

A reasonable pilot setting is top 5 retrieved files and a fixed context budget that fits the selected LLM. Top 5 is useful because the retrieval study shows meaningful differences between Recall@5 and Recall@10; a later ablation can compare context depths.

## Controlled LLM setup

Hold the following constant:

- LLM model and exact model version;
- system and user prompts;
- temperature (preferably 0) and other sampling parameters;
- context-token budget and truncation procedure;
- answer-token limit;
- anchor context;
- question wording;
- output schema;
- number of attempts per task and condition.

The retrieval method is the primary independent variable. Run condition order in a randomized or counterbalanced sequence, and store prompts, contexts, model metadata, and raw responses for reproducibility.

## Suggested answer schema

Require structured answers with:

1. affected components/files;
2. explanation of the repository relationship;
3. expected behavioral or API impact;
4. tests/configuration that should be updated;
5. file-path citations supporting each claim;
6. an explicit “insufficient evidence” option.

## Evaluation

Evaluate answers without showing graders which retrieval method produced them.

### Correctness

- coverage of gold files or gold components;
- correctness of described behavior;
- correctness of cross-file relationships;
- absence of contradicted claims.

### Groundedness

- fraction of substantive claims supported by supplied context;
- citation correctness: cited path actually supports the claim;
- hallucinated files, symbols, or behavior;
- appropriate acknowledgment when context is insufficient.

### Scoring procedure

- Develop a small rubric with ordinal scores, for example 0–2 for component identification, behavioral explanation, test/configuration implications, and grounded citations.
- Use at least two blinded graders for a subset if feasible and report agreement.
- Separately record whether the answer names each gold file; do not treat file-name overlap alone as full QA correctness.
- Compare conditions within each task because the same question is answered with three different retrieved contexts.

## Analysis

- Report per-task scores and paired differences rather than only averages.
- Relate QA outcomes to retrieval Recall@5 and reciprocal rank without assuming causality from correlation.
- Examine whether hybrid context helps when it combines different relevant files and whether extra irrelevant files reduce answer quality.
- Treat the eight-task pilot as exploratory. Do not run significance tests unless the final sample and scoring procedure justify them.

## Decision criterion for a larger extension

Proceed to a larger downstream study only if the pilot shows that the rubric is reliable, the prompt is stable, contexts fit within a controlled budget, and answer differences can be traced to retrieved evidence rather than prompt or truncation artifacts.

## Not included in this week

This plan does not make LLM API calls, select a production model, implement prompt execution, or tune retrieval parameters. Those actions should occur only after the pilot tasks, context budget, rubric, and model-cost limits are approved.
