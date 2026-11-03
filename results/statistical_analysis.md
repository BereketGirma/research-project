# Paired statistical analysis

## Method

All comparisons use the same 58 tasks. A two-sided Wilcoxon signed-rank test compares paired per-task scores. Because the metrics are discrete and contain many ties, zero differences are excluded (`zero_method=wilcox`) and asymptotic p-values are reported. The test therefore evaluates the rank distribution of nonzero paired differences, not merely the difference in means.

The unadjusted decision threshold is α = 0.05. Holm-adjusted p-values are also reported across the nine tests to make the multiple-comparison sensitivity explicit. Wilcoxon assumes that nonzero paired differences are approximately symmetric; given the discrete metrics and modest effective sample sizes, results should be interpreted cautiously.

## Results

| Comparison | Metric | W | p | Nonzero / paired | Significant (α=.05) | Holm p | Holm significant |
|---|---|---:|---:|---:|---|---:|---|
| BM25 vs Semantic | Recall@5 | 137.000 | 0.481098 | 25 / 58 | False | 0.962195 | False |
| BM25 vs Semantic | Recall@10 | 94.000 | 0.967330 | 19 / 58 | False | 0.967330 | False |
| BM25 vs Semantic | Reciprocal rank | 255.500 | 0.147302 | 37 / 58 | False | 0.908643 | False |
| BM25 vs Hybrid RRF | Recall@5 | 16.500 | 0.243946 | 10 / 58 | False | 0.908643 | False |
| BM25 vs Hybrid RRF | Recall@10 | 22.500 | 0.191389 | 12 / 58 | False | 0.908643 | False |
| BM25 vs Hybrid RRF | Reciprocal rank | 120.500 | 0.162108 | 26 / 58 | False | 0.908643 | False |
| Semantic vs Hybrid RRF | Recall@5 | 40.500 | 0.046543 | 18 / 58 | True | 0.372340 | False |
| Semantic vs Hybrid RRF | Recall@10 | 28.500 | 0.129806 | 14 / 58 | False | 0.908643 | False |
| Semantic vs Hybrid RRF | Reciprocal rank | 85.000 | 0.004149 | 29 / 58 | True | 0.037344 | True |

## Interpretation

Statistical significance is determined from paired task-level differences, not from aggregate means alone. A non-significant result does not establish equivalence; it means this sample does not provide sufficient evidence of a systematic paired difference under this test. Conversely, an unadjusted p-value below 0.05 should be considered alongside the Holm result because nine related hypotheses were tested.
