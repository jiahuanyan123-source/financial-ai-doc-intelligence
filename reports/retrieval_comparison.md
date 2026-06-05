# Retrieval Comparison

This table compares retrieval baselines on the public-safe multi-document
fixture. It is a citation-control comparison, not an LLM answer-quality
benchmark.

## Dataset

- Eval file: `examples/multi_doc_rag_eval_cases.json`
- Documents: 3 synthetic issuer notes
- Cases: 4
- Top-k: 5 retrieved lines per case

## Results

| Retriever | Status | Line recall@k | Term coverage@k | Source hit@k | Distractor leak@k | Pass rate | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Token overlap + one-line context | Previous public baseline | 75.00% | 91.67% | 100.00% | 35.00% | 25.00% | Found the right source document, but mixed in peer and sector distractors. |
| Source-prior token overlap | Current public baseline | 87.50% | 91.67% | 100.00% | 5.00% | 50.00% | Adds a lightweight source-label prior when query tokens match document labels. |
| Local embedding retrieval | Not implemented | N/A | N/A | N/A | N/A | N/A | Next candidate. Must beat the source-prior baseline before being promoted. |

## Verification

Current source-prior metrics were regenerated locally with:

```bash
PYTHONPATH=src python -m finai_docintelligence eval-rag examples/multi_doc_rag_eval_cases.json --out reports/multi_doc_rag_eval_report.md --json reports/multi_doc_rag_eval_report.json
```

Unit tests were also run locally:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Remaining Failure Modes

- One North River external-guarantee case still misses one expected line.
- One North River liquidity case still leaks one East Bay peer line into top-k.
- The source-prior approach depends on source-label tokens appearing in the
  query, so it may not generalize to ambiguous issuer names or unlabeled user
  questions.

## Next Test

Implement local embedding retrieval only as a controlled comparison. It should
keep the same fixture, top-k, and metrics so the result is comparable with the
two deterministic baselines above.
