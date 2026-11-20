from __future__ import annotations

import unittest
from pathlib import Path

from finai_docintelligence.embedding_sensitivity import (
    evaluate_embedding_dimension_sensitivity,
    render_embedding_sensitivity_markdown,
)


ROOT = Path(__file__).resolve().parents[1]
MULTI_DOC_CASES = ROOT / "examples" / "multi_doc_rag_eval_cases.json"


class EmbeddingSensitivityTests(unittest.TestCase):
    def test_dimension_sensitivity_reports_all_dimensions(self) -> None:
        report = evaluate_embedding_dimension_sensitivity(MULTI_DOC_CASES, dimensions=(32, 64, 128, 256))

        self.assertEqual(report.dimensions, (32, 64, 128, 256))
        self.assertEqual([result.dimensions for result in report.results], [32, 64, 128, 256])
        self.assertEqual(report.best_dimensions, (128,))
        self.assertTrue(report.worst_dimensions)

    def test_dimension_sensitivity_exposes_dimension_dependence(self) -> None:
        report = evaluate_embedding_dimension_sensitivity(MULTI_DOC_CASES, dimensions=(32, 64, 128, 256))

        pass_rates = {result.dimensions: result.pass_rate for result in report.results}
        self.assertEqual(pass_rates[128], 1.0)
        self.assertLess(min(pass_rates.values()), max(pass_rates.values()))

    def test_dimension_sensitivity_markdown_names_limitations(self) -> None:
        report = evaluate_embedding_dimension_sensitivity(MULTI_DOC_CASES, dimensions=(128,))
        markdown = render_embedding_sensitivity_markdown(report)

        self.assertIn("not a neural embedding model", markdown)
        self.assertIn("fixture-specific", markdown)


if __name__ == "__main__":
    unittest.main()
