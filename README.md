# Repository context retrieval experiments

Lexical and semantic file retrieval baselines for the Agent Retrieval Bench
`v2_edit2ripple` subset. The downloaded benchmark is expected in the sibling
checkout `../agent-retrieval-bench/data/` by default; all paths can be
overridden with command-line flags.

Both baselines use the same experimental setup:

- query: `query.intent + query.anchor_diff`
- chunk document: `path + symbol + chunk text`
- exact `repo + base_commit` corpus snapshot
- anchor file excluded from ranked results
- chunk scores deduplicated to files by the highest-scoring chunk
- file-level Recall@5, Recall@10, and reciprocal rank at retrieval depth 10

## BM25

```sh
.venv/bin/python experiments/run_bm25.py
.venv/bin/python experiments/analyze_bm25_first10.py
.venv/bin/python experiments/plot_results.py
```

The first-10 BM25 file is reproducible with:

```sh
.venv/bin/python experiments/run_bm25.py \
  --limit 10 \
  --output results/bm25_edit2ripple_first10.csv \
  --summary results/bm25_edit2ripple_first10_summary.json
```

## Semantic baseline

The semantic baseline uses
`sentence-transformers/all-MiniLM-L6-v2`, CPU inference, normalized embeddings,
and direct cosine similarity (the dot product of normalized vectors). Model
inputs use the same query and document fields as BM25. Sentence Transformers
applies the model's standard maximum sequence length when encoding long chunks.

```sh
.venv/bin/python experiments/run_semantic.py --limit 10
.venv/bin/python experiments/compare_first10.py
```

The model is downloaded from Hugging Face on the first run if it is not already
cached. No FAISS index is needed for this experiment size.
