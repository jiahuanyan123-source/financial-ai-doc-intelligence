# Embedding Public Readiness Check

Status: `pass`
Checks: 15
Failures: 0

Local hashing embedding evidence is bounded by sensitivity caveats.

This gate does not validate real neural embedding quality. It only checks
that the deterministic local hashing comparison keeps its limitations visible
before the result is copied into public portfolio language.

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| file_exists:reports\retrieval_comparison.md | pass | required embedding evidence file |
| file_exists:reports\embedding_dimension_sensitivity.md | pass | required embedding evidence file |
| file_exists:reports\embedding_dimension_sensitivity.json | pass | required embedding evidence file |
| file_exists:reports\embedding_rag_eval_report.json | pass | required embedding evidence file |
| comparison_caveat:not_neural | pass | retrieval comparison must not frame hashing as neural embedding quality |
| comparison_caveat:dimension_sensitive | pass | retrieval comparison must show that the hashing result depends on dimension choice |
| comparison_caveat:no_semantic_quality_claim | pass | retrieval comparison must avoid promoting the toy result as semantic retrieval quality |
| sensitivity_caveat:not a neural embedding model | pass | dimension sensitivity report must keep limitations visible |
| sensitivity_caveat:fixture-specific | pass | dimension sensitivity report must keep limitations visible |
| sensitivity_caveat:does not prove answer quality | pass | dimension sensitivity report must keep limitations visible |
| sensitivity_dimensions | pass | observed dimensions: [32, 64, 128, 256] |
| dimension_dependence_visible | pass | embedding pass_rate=1.0; sensitivity pass rates={32: 0.0, 64: 0.0, 128: 1.0, 256: 0.75} |
| failed_dimensions_visible | pass | worst_dimensions=[32, 64] |
| non_128_leak_visible | pass | distractor leak rates={32: 0.25, 64: 0.15000000000000002, 128: 0.0, 256: 0.05} |
| embedding_not_promoted_to_production | pass | report must explicitly avoid production-readiness claims |
