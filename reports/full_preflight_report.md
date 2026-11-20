# Full Local Preflight Report

Status: `pass`
Repository: `financial-ai-doc-intelligence`
Generated UTC: `not_recorded_for_deterministic_report`
Steps: 9 / 9
Failures: 0

All local Financial RAG release checks passed.

This report is a local publication gate for the deterministic Financial RAG
baseline. It does not prove production RAG quality, credit judgment quality,
or neural embedding performance.

## Checks

| Step | Status | Command |
| --- | --- | --- |
| unit_tests | pass | `python -m unittest discover -s tests` |
| sample_analysis_report | pass | `python -m finai_docintelligence analyze examples/sample_issuer_credit_note.md --out reports/sample_report.md --json reports/sample_report.json` |
| single_document_rag_eval | pass | `python -m finai_docintelligence eval-rag examples/rag_eval_cases.json --out reports/rag_eval_report.md --json reports/rag_eval_report.json` |
| multi_document_rag_eval | pass | `python -m finai_docintelligence eval-rag examples/multi_doc_rag_eval_cases.json --out reports/multi_doc_rag_eval_report.md --json reports/multi_doc_rag_eval_report.json` |
| hashing_embedding_eval | pass | `python -m finai_docintelligence eval-rag examples/multi_doc_rag_eval_cases.json --retriever hashing-embedding --embedding-dimensions 128 --out reports/embedding_rag_eval_report.md --json reports/embedding_rag_eval_report.json` |
| embedding_dimension_sensitivity | pass | `python -m finai_docintelligence embedding-sensitivity examples/multi_doc_rag_eval_cases.json --dimensions 32,64,128,256 --out reports/embedding_dimension_sensitivity.md --json reports/embedding_dimension_sensitivity.json` |
| embedding_public_readiness | pass | `python tools/embedding_public_readiness_check.py --json reports/embedding_public_readiness_report.json --markdown reports/embedding_public_readiness_report.md` |
| repository_manifest | pass | `python tools/repository_manifest.py --json reports/repository_manifest.json --markdown reports/repository_manifest.md` |
| repository_manifest_verify | pass | `python tools/repository_manifest.py --verify --json reports/repository_manifest.json` |
