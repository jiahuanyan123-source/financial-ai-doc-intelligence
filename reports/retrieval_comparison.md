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
| Local hashing embedding retrieval | Local deterministic comparison | 100.00% | 100.00% | 100.00% | 0.00% | 100.00% | Uses a 128-dimension lexical hashing backend; this is not a neural embedding model or external API benchmark. See sensitivity check below before interpreting the win. |

## Hashing Dimension Sensitivity

The hashing result is not stable across all dimensions on the toy fixture.
This check prevents the 128-dimension result from being presented as a robust
semantic retrieval claim.

| Dimensions | Line recall@k | Term coverage@k | Source hit@k | Distractor leak@k | Pass rate |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 50.00% | 66.67% | 100.00% | 25.00% | 0.00% |
| 64 | 62.50% | 79.17% | 100.00% | 15.00% | 0.00% |
| 128 | 100.00% | 100.00% | 100.00% | 0.00% | 100.00% |
| 256 | 100.00% | 100.00% | 100.00% | 5.00% | 75.00% |

## Verification

Current source-prior metrics were regenerated locally with:

```bash
PYTHONPATH=src python -m finai_docintelligence eval-rag examples/multi_doc_rag_eval_cases.json --out reports/multi_doc_rag_eval_report.md --json reports/multi_doc_rag_eval_report.json
PYTHONPATH=src python -m finai_docintelligence eval-rag examples/multi_doc_rag_eval_cases.json --retriever hashing-embedding --embedding-dimensions 128 --out reports/embedding_rag_eval_report.md --json reports/embedding_rag_eval_report.json
PYTHONPATH=src python -m finai_docintelligence embedding-sensitivity examples/multi_doc_rag_eval_cases.json --dimensions 32,64,128,256 --out reports/embedding_dimension_sensitivity.md --json reports/embedding_dimension_sensitivity.json
```

Unit tests were also run locally:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Remaining Failure Modes

- The source-prior baseline still misses one North River external-guarantee line.
- The source-prior baseline still leaks one East Bay peer line into top-k.
- The source-prior approach depends on source-label tokens appearing in the
  query, so it may not generalize to ambiguous issuer names or unlabeled user
  questions.
- The hashing embedding baseline is perfect on this toy fixture, but it is
  still lexical, source-label-aware, and too small to prove semantic retrieval
  quality.
- The hashing embedding baseline is dimension-sensitive: 32 and 64 dimensions
  fail all cases, while 256 dimensions reintroduces a small distractor leak.

## Next Test

Attach a real local neural embedding backend only as a controlled comparison.
It should keep the same fixture, top-k, and metrics so the result is comparable
with the deterministic baselines above.

Implementation plan: [docs/embedding_retrieval_comparison_plan.md](../docs/embedding_retrieval_comparison_plan.md).
