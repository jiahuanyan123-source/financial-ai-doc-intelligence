from __future__ import annotations

import unittest
from pathlib import Path
from typing import Sequence

from finai_docintelligence.embedding_retrieval import (
    EmbeddingRetrieverUnavailable,
    embed_texts_with_hashing,
)
from finai_docintelligence.evaluation import evaluate_case, evaluate_cases, load_cases
from finai_docintelligence.retrieval import retrieve_lines


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample_issuer_credit_note.md"
CASES = ROOT / "examples" / "rag_eval_cases.json"
MULTI_DOC_CASES = ROOT / "examples" / "multi_doc_rag_eval_cases.json"


class RetrievalEvalTests(unittest.TestCase):
    def test_retrieves_expected_liquidity_lines(self) -> None:
        results = retrieve_lines(str(SAMPLE), "short-term debt and cash position", top_k=3)
        line_numbers = {item.line_number for item in results}

        self.assertIn(23, line_numbers)
        self.assertIn(24, line_numbers)

    def test_retrieval_result_carries_source_label(self) -> None:
        results = retrieve_lines(
            str(SAMPLE),
            "short-term debt and cash position",
            top_k=1,
            source_label="sample_issuer_credit_note.md",
        )

        self.assertEqual(results[0].source, "sample_issuer_credit_note.md")

    def test_rag_eval_baseline_passes_sample_cases(self) -> None:
        report = evaluate_cases(CASES, top_k=5)

        self.assertEqual(len(report.cases), 4)
        self.assertGreaterEqual(report.average_line_recall, 1.0)
        self.assertGreaterEqual(report.average_term_coverage, 0.8)
        self.assertEqual(report.average_source_hit, 1.0)
        self.assertEqual(report.average_distractor_leak_rate, 0.0)
        self.assertEqual(report.pass_rate, 1.0)

    def test_multi_doc_eval_reports_source_and_distractor_metrics(self) -> None:
        report = evaluate_cases(MULTI_DOC_CASES, top_k=5)

        self.assertEqual(len(report.cases), 4)
        self.assertEqual(report.average_source_hit, 1.0)
        self.assertLessEqual(report.average_distractor_leak_rate, 0.05)
        self.assertGreaterEqual(report.pass_rate, 0.5)
        self.assertTrue(all(item.retrieved_lines for item in report.cases))

    def test_embedding_retriever_requires_explicit_backend(self) -> None:
        with self.assertRaises(EmbeddingRetrieverUnavailable):
            evaluate_cases(MULTI_DOC_CASES, top_k=5, retriever="embedding")

    def test_embedding_retriever_can_be_selected_with_injected_backend(self) -> None:
        def embed_texts(texts: Sequence[str]) -> list[list[float]]:
            vectors: list[list[float]] = []
            for text in texts:
                lowered = text.lower()
                vectors.append(
                    [
                        1.0 if "north river" in lowered else 0.0,
                        1.0 if "short-term debt" in lowered else 0.0,
                        1.0 if "cash" in lowered else 0.0,
                        1.0 if "external guarantees" in lowered else 0.0,
                        1.0 if "east bay" in lowered else 0.0,
                        1.0 if "harbor city" in lowered else 0.0,
                        1.0 if "government grants" in lowered else 0.0,
                    ]
                )
            return vectors

        result = evaluate_case(load_cases(MULTI_DOC_CASES)[0], top_k=5, retriever="embedding", embed_texts=embed_texts)
        retrieved_target_lines = {item.line_number for item in result.retrieved_lines if item.source == result.source}

        self.assertEqual(result.source_hit, 1.0)
        self.assertIn(23, retrieved_target_lines)
        self.assertIn(24, retrieved_target_lines)

    def test_hashing_embedding_backend_is_deterministic(self) -> None:
        first = embed_texts_with_hashing(["North River cash position"], dimensions=128)
        second = embed_texts_with_hashing(["North River cash position"], dimensions=128)

        self.assertEqual(first, second)
        self.assertEqual(len(first[0]), 128)

    def test_hashing_embedding_eval_passes_toy_multi_doc_fixture(self) -> None:
        report = evaluate_cases(
            MULTI_DOC_CASES,
            top_k=5,
            retriever="embedding",
            embed_texts=lambda texts: embed_texts_with_hashing(texts, dimensions=128),
        )

        self.assertEqual(report.average_line_recall, 1.0)
        self.assertEqual(report.average_term_coverage, 1.0)
        self.assertEqual(report.average_source_hit, 1.0)
        self.assertEqual(report.average_distractor_leak_rate, 0.0)
        self.assertEqual(report.pass_rate, 1.0)
        self.assertEqual(report.retriever, "embedding")


if __name__ == "__main__":
    unittest.main()
