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

## Candidate Implementation

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

Add a small embedding retrieval module and a test that proves the new retriever
can be selected without changing the deterministic default path.
