# Financial AI Document Intelligence

Portfolio project 01 for a finance-to-AI transition.

This project builds a baseline credit-document analysis and evaluation system. It ingests a
plain-text or Markdown issuer note, extracts structured financial facts,
computes credit metrics, flags risks with source-line citations, and generates
an analyst-style memo. It also includes a small deterministic RAG-style
retrieval evaluation that checks whether questions retrieve the expected
evidence lines.

The first version is intentionally deterministic and dependency-light. The goal
is to build a clean baseline before adding LLM, RAG, vector search, and agentic
workflows.

## Why This Project Matters

Financial AI systems fail when they cannot control facts, numbers, citations,
and workflow boundaries. A useful LLM system needs:

- a clearly defined task,
- structured inputs and outputs,
- deterministic baselines,
- measurable quality checks,
- citations and human review hooks.

This repository starts from those foundations.

## What It Does

- Parses issuer credit notes from `.txt` or `.md` files.
- Extracts issuer metadata and financial fields.
- Computes leverage, liquidity, interest coverage, debt intensity, and free cash flow.
- Flags credit risks with source-line citations.
- Generates Markdown and JSON reports.
- Runs a deterministic citation-retrieval eval over public-safe sample cases.
- Includes tests for parsing, metric calculation, and risk detection.

## Quick Start

```bash
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

```bash
python -m finai_docintelligence analyze examples/sample_issuer_credit_note.md --out reports/sample_report.md --json reports/sample_report.json
```

```bash
python -m finai_docintelligence eval-rag examples/rag_eval_cases.json --out reports/rag_eval_report.md --json reports/rag_eval_report.json
```

```bash
python -m finai_docintelligence eval-rag examples/multi_doc_rag_eval_cases.json --out reports/multi_doc_rag_eval_report.md --json reports/multi_doc_rag_eval_report.json
```

On macOS/Linux:

```bash
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m finai_docintelligence analyze examples/sample_issuer_credit_note.md --out reports/sample_report.md --json reports/sample_report.json
PYTHONPATH=src python -m finai_docintelligence eval-rag examples/rag_eval_cases.json --out reports/rag_eval_report.md --json reports/rag_eval_report.json
PYTHONPATH=src python -m finai_docintelligence eval-rag examples/multi_doc_rag_eval_cases.json --out reports/multi_doc_rag_eval_report.md --json reports/multi_doc_rag_eval_report.json
```

## Project Structure

```text
financial-ai-doc-intelligence/
  src/finai_docintelligence/
    analyzer.py
    cli.py
    evaluation.py
    model.py
    report.py
    retrieval.py
  examples/
    multi_doc/
      city_utility_distractor.md
      east_bay_peer.md
      north_river_target.md
    multi_doc_rag_eval_cases.json
    rag_eval_cases.json
    sample_issuer_credit_note.md
  reports/
    .gitkeep
  tests/
    test_analyzer.py
  docs/
    lesson_01.md
    multi_doc_eval_checklist.md
```

## Roadmap

- v0: deterministic parser, metrics, risk flags, citations.
- v1: add deterministic RAG eval cases and scoring for citation retrieval.
- v2: add extraction accuracy evals and multi-document issuer packages.
- v3: add local embeddings and RAG over multi-document issuer packages.
- v4: add LLM-based report drafting with strict citation validation.
- v5: add an analyst-in-the-loop review UI.

Next implementation checklist: [docs/multi_doc_eval_checklist.md](docs/multi_doc_eval_checklist.md).

## Current Evaluation Baseline

The first RAG eval uses synthetic, public-safe issuer notes and a token-overlap
retriever with one-line neighbor expansion. It checks:

- expected source-line recall@k,
- expected term coverage@k,
- whether each case has enough evidence to support an answer.

This is intentionally not an LLM benchmark yet. It is the citation-control layer
that later LLM outputs must satisfy.

The multi-document fixture originally exposed a useful failure mode: the
baseline could find the right source document while still mixing in peer or
sector distractor evidence. The current lightweight source-prior retriever
improves that baseline to 87.50% line recall@k, 100.00% source document hit@k,
5.00% distractor leak rate@k, and 50.00% pass rate.

This is still not production RAG. It is a measurable retrieval-control baseline
that makes the remaining failure visible before adding embeddings or LLM calls.

Comparison table: [reports/retrieval_comparison.md](reports/retrieval_comparison.md).
Embedding comparison plan: [docs/embedding_retrieval_comparison_plan.md](docs/embedding_retrieval_comparison_plan.md).

## Portfolio Signal

This project is designed to show:

- finance-domain judgment,
- AI task decomposition,
- clean Python engineering,
- test discipline,
- evaluable outputs,
- a credible path from rules to LLM systems.
