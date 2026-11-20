from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "embedding_public_readiness_check.py"
SPEC = importlib.util.spec_from_file_location("embedding_public_readiness_check", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
embedding_public_readiness_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(embedding_public_readiness_check)


class EmbeddingPublicReadinessTests(unittest.TestCase):
    def test_current_embedding_reports_pass_public_readiness(self) -> None:
        report = embedding_public_readiness_check.evaluate_public_embedding_readiness(ROOT)

        self.assertEqual(report["status"], "pass")
        check_names = {check["name"] for check in report["checks"]}
        self.assertIn("dimension_dependence_visible", check_names)
        self.assertIn("failed_dimensions_visible", check_names)

    def test_missing_sensitivity_caveats_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            (reports / "retrieval_comparison.md").write_text(
                "not a neural embedding benchmark\n"
                "dimension-sensitive\n"
                "robust semantic retrieval quality\n",
                encoding="utf-8",
            )
            (reports / "embedding_dimension_sensitivity.md").write_text(
                "This report only lists metrics.\n",
                encoding="utf-8",
            )
            (reports / "embedding_rag_eval_report.json").write_text(
                json.dumps({"pass_rate": 1.0}),
                encoding="utf-8",
            )
            (reports / "embedding_dimension_sensitivity.json").write_text(
                json.dumps(
                    {
                        "results": [
                            {"dimensions": 32, "pass_rate": 0.0, "average_distractor_leak_rate": 0.25},
                            {"dimensions": 64, "pass_rate": 0.0, "average_distractor_leak_rate": 0.15},
                            {"dimensions": 128, "pass_rate": 1.0, "average_distractor_leak_rate": 0.0},
                            {"dimensions": 256, "pass_rate": 0.75, "average_distractor_leak_rate": 0.05},
                        ],
                        "worst_dimensions": [32, 64],
                    }
                ),
                encoding="utf-8",
            )

            report = embedding_public_readiness_check.evaluate_public_embedding_readiness(root)

        self.assertEqual(report["status"], "fail")
        failed_checks = {check["name"] for check in report["checks"] if check["status"] == "fail"}
        self.assertIn("sensitivity_caveat:not a neural embedding model", failed_checks)
        self.assertIn("embedding_not_promoted_to_production", failed_checks)
