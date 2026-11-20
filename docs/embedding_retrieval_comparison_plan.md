# Embedding Retrieval Comparison Plan

This plan defines how to test local embedding retrieval without turning the
project into an unverified model demo.

## Goal

Compare a local embedding retriever against the current source-prior baseline
on the same public-safe multi-document fixture.

The embedding retriever should only be promoted if it improves the published
metrics without hiding new failure modes.

## Fixed Evaluation Contract

- Eval file: `examples/multi_doc_rag_eval_cases.json`
- Documents: 3 synthetic issuer notes
- Cases: 4
- Top-k: 5 retrieved lines per case
- Metrics:
  - line recall@k
  - expected-term coverage@k
  - source document hit@k
  - distractor leak rate@k
  - pass rate

## Current Baseline To Beat

| Retriever | Line recall@k | Term coverage@k | Source hit@k | Distractor leak@k | Pass rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Source-prior token overlap | 87.50% | 91.67% | 100.00% | 5.00% | 50.00% |

## Completed Local Hashing Baseline

The second implementation slice adds a deterministic local hashing-embedding
backend. It has no model download, no external API, and no network dependency.
On the fixed toy multi-document fixture, it produced:

| Retriever | Line recall@k | Term coverage@k | Source hit@k | Distractor leak@k | Pass rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Local hashing embedding, 128 dimensions | 100.00% | 100.00% | 100.00% | 0.00% | 100.00% |

This is a dependency-free acceptance baseline for the embedding selector and
comparison workflow. It is not a neural embedding model and should not be
described as semantic retrieval quality.

## Dimension Sensitivity Check

The hashing baseline now includes a dimension-sensitivity report to avoid
promoting a single cherry-picked configuration.

| Dimensions | Line recall@k | Term coverage@k | Source hit@k | Distractor leak@k | Pass rate |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 50.00% | 66.67% | 100.00% | 25.00% | 0.00% |
| 64 | 62.50% | 79.17% | 100.00% | 15.00% | 0.00% |
| 128 | 100.00% | 100.00% | 100.00% | 0.00% | 100.00% |
| 256 | 100.00% | 100.00% | 100.00% | 5.00% | 75.00% |

Interpretation: the hashing backend is useful as a reproducible acceptance
baseline, but it is dimension-sensitive on the toy fixture. The 128-dimension
result should be described as a local deterministic comparison, not robust
semantic retrieval quality.

## Candidate Neural Implementation

Start with a local sentence-embedding model only after keeping the deterministic
baseline runnable without extra dependencies.

Preferred implementation boundary:

- Keep the existing default CLI path dependency-light.
- Put embedding retrieval behind an explicit CLI option or separate command.
- Do not require network access during evaluation.
- Document the model name, model size, dependency, and local cache behavior.
- If model download is needed, document that separately and keep CI on the
  deterministic baseline unless the model can be cached safely.

## Promotion Rules

Promote embedding retrieval only if:

- line recall@k is at least 87.50%,
- distractor leak@k is no worse than 5.00%,
- pass rate is higher than 50.00%, or a clear failure mode is reduced,
- unit tests still pass,
- the comparison report shows both wins and losses.

Do not promote it if it only sounds more advanced while metrics stay the same
or get worse.

## Failure Reporting

If embedding retrieval underperforms, update
`reports/retrieval_comparison.md` with the failed metrics and likely reasons.
That failure is still useful evidence because it shows disciplined evaluation.

## Next Implementation Slice

Completed first slice: add a small embedding retrieval module and tests proving
the retriever can be selected without changing the deterministic default path.

Completed second slice: add a deterministic hashing-embedding backend, CLI
option, generated Markdown/JSON reports, CI command, and comparison-table
metrics.

Completed third slice: add a dimension-sensitivity command and report showing
that the 128-dimension hashing win is not stable across all dimensions.

Next slice: choose a local neural embedding backend, document the
dependency/cache behavior, then run the same multi-document comparison and the
sensitivity report before promoting any metric.
