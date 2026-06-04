# Multi-Document RAG Eval Checklist

This checklist defines the next verified step after the v0 single-document
retrieval baseline. It is intentionally narrow: prove source attribution under
distractor documents before adding heavier model components.

## Objective

Build a synthetic multi-document evaluation fixture that checks whether retrieval
returns evidence from the correct source document and line range when relevant
and irrelevant issuer notes are mixed together.

## Fixture Scope

- Use only synthetic, public-safe documents.
- Include one target issuer note with liquidity, debt, guarantees, and support
  facts.
- Include at least two distractor documents:
  - a peer issuer with similar financial vocabulary but different numbers,
  - an unrelated infrastructure note with overlapping terms.
- Keep documents short enough that expected source lines can be manually audited.

## Case Requirements

Each eval case should include:

- `case_id`
- `question`
- expected source document
- expected source lines
- required terms
- optional forbidden source documents for distractor checks

## Metrics

The first multi-doc report should include:

- source document hit@k,
- expected source-line recall@k,
- expected-term coverage@k,
- distractor leak rate,
- pass/fail status per case.

## Acceptance Criteria

- The CLI can run the multi-document eval from one command.
- Unit tests cover case parsing and at least one distractor failure mode.
- The report includes both passing and failing evidence rows when applicable.
- The README links to the multi-doc report without claiming production RAG
  quality.
- Limitations clearly state that the fixture is synthetic and not an LLM
  benchmark.

## Implementation Order

1. Add synthetic document fixtures under `examples/multi_doc/`.
2. Add a JSON eval case file for multi-doc retrieval.
3. Extend retrieval/evaluation code only as much as needed to carry source
   labels through scoring.
4. Add tests for source labels and distractor leakage.
5. Generate `reports/multi_doc_rag_eval_report.md` and a JSON artifact.
6. Update README with the exact command and limitations.
