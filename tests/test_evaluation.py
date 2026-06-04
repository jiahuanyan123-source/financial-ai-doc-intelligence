from __future__ import annotations

import unittest
from pathlib import Path

from finai_docintelligence.evaluation import evaluate_cases
from finai_docintelligence.retrieval import retrieve_lines


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample_issuer_credit_note.md"
CASES = ROOT / "examples" / "rag_eval_cases.json"


class RetrievalEvalTests(unittest.TestCase):
    def test_retrieves_expected_liquidity_lines(self) -> None:
        results = retrieve_lines(str(SAMPLE), "short-term debt and cash position", top_k=3)
        line_numbers = {item.line_number for item in results}

        self.assertIn(23, line_numbers)
        self.assertIn(24, line_numbers)

    def test_rag_eval_baseline_passes_sample_cases(self) -> None:
        report = evaluate_cases(CASES, top_k=5)

        self.assertEqual(len(report.cases), 4)
        self.assertGreaterEqual(report.average_line_recall, 1.0)
        self.assertGreaterEqual(report.average_term_coverage, 0.8)
        self.assertEqual(report.pass_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
