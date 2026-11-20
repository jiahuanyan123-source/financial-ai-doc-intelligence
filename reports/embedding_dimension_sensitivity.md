# Embedding Dimension Sensitivity Report

This report checks whether the deterministic local hashing-embedding result
is stable across vector dimensions on the same public-safe multi-document
fixture.

## Evaluation Contract

- Eval file: `examples/multi_doc_rag_eval_cases.json`
- Top-k: 5
- Retriever: deterministic local hashing embedding
- External model/API calls: none

## Results

| Dimensions | Line recall@k | Term coverage@k | Source hit@k | Distractor leak@k | Pass rate |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 50.00% | 66.67% | 100.00% | 25.00% | 0.00% |
| 64 | 62.50% | 79.17% | 100.00% | 15.00% | 0.00% |
| 128 | 100.00% | 100.00% | 100.00% | 0.00% | 100.00% |
| 256 | 100.00% | 100.00% | 100.00% | 5.00% | 75.00% |

## Finding

- Best pass rate: 100.00% at dimensions 128.
- Worst pass rate: 0.00% at dimensions 32, 64.
- The 128-dimension result should be treated as fixture-specific until
  it is repeated with a real local neural embedding backend and broader
  issuer-document cases.

## Limitations

- This is a deterministic lexical hashing backend, not a neural embedding model.
- The fixture is synthetic and intentionally small.
- Passing this report does not prove answer quality or production RAG readiness.
