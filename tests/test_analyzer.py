from __future__ import annotations

import unittest
from pathlib import Path

from finai_docintelligence.analyzer import analyze


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample_issuer_credit_note.md"


class AnalyzerTests(unittest.TestCase):
    def test_extracts_core_fields(self) -> None:
        result = analyze(SAMPLE)

        self.assertEqual(result.fields["issuer"].value, "North River Infrastructure Group")
        self.assertEqual(result.fields["rating"].value, "AAA")
        self.assertEqual(result.fields["industry"].value, "Transportation Infrastructure")
        self.assertEqual(result.fields["total_debt"].value, 78.0)

    def test_computes_credit_metrics(self) -> None:
        result = analyze(SAMPLE)

        self.assertAlmostEqual(result.metrics["debt_to_ebitda"].value, 78.0 / 8.2, places=4)
        self.assertAlmostEqual(result.metrics["cash_to_short_term_debt"].value, 12.0 / 18.5, places=4)
        self.assertAlmostEqual(result.metrics["interest_coverage"].value, 8.2 / 2.4, places=4)
        self.assertAlmostEqual(result.metrics["free_cash_flow"].value, 5.1 - 9.8, places=4)

    def test_detects_risk_flags(self) -> None:
        result = analyze(SAMPLE)
        categories = {risk.category for risk in result.risks}

        self.assertIn("Leverage", categories)
        self.assertIn("Liquidity", categories)
        self.assertIn("Cash flow", categories)
        self.assertIn("Capital structure", categories)
        self.assertIn("Contingent liability", categories)
        self.assertNotIn("Legal risk", categories)

    def test_generates_analyst_questions(self) -> None:
        result = analyze(SAMPLE)

        self.assertTrue(any("short-term debt" in question for question in result.analyst_questions))
        self.assertTrue(any("capex" in question for question in result.analyst_questions))


if __name__ == "__main__":
    unittest.main()
