# Document Version Review Demo

Comparing two versions of a business document is useful only when a reviewer can
see both versions of the changed text. This small offline demo isolates that
step using two invented service-policy drafts. It does not include or derive
text from any real document or internal workflow implementation.

```bash
python tools/compare_document_versions.py examples/document_versions.json
```

The fixture changes a response window from 3 to 5 business days, removes a draft
summary requirement, and adds a review step. The report marks each section as
`changed`, `removed`, or `added` and gives its before/after text (or `null` when
absent). Whitespace-only edits are ignored.

**Input contract:** a JSON object with `before` and `after` arrays. Each item
has a stable text `id` and `text`. Duplicate IDs in either version are rejected
instead of overwriting a section.

**Limitations:** this demo starts from already segmented text; it does not
perform OCR, PDF alignment, extraction, clause matching, or legal analysis.
Changing an ID is reported as a removal and addition, and reordering alone is
not reported. Human review is required for meaning and impact.
