from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "run_full_preflight.py"
SPEC = importlib.util.spec_from_file_location("run_full_preflight", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
run_full_preflight = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_full_preflight
SPEC.loader.exec_module(run_full_preflight)


class FullPreflightContractTests(unittest.TestCase):
    def test_preflight_steps_cover_embedding_publication_gate(self) -> None:
        steps = run_full_preflight.build_preflight_steps()
        step_names = [step.name for step in steps]

        self.assertEqual(step_names[0], "unit_tests")
        self.assertIn("hashing_embedding_eval", step_names)
        self.assertIn("embedding_dimension_sensitivity", step_names)
        self.assertIn("embedding_public_readiness", step_names)
        self.assertEqual(step_names[-2:], ["repository_manifest", "repository_manifest_verify"])

    def test_markdown_keeps_limitations_visible(self) -> None:
        report = {
            "status": "pass",
            "repository": "financial-ai-doc-intelligence",
            "generated_at_utc": "2026-06-12T00:00:00+00:00",
            "step_count": 1,
            "expected_step_count": 1,
            "failure_count": 0,
            "summary": "All local Financial RAG release checks passed.",
            "checks": [{"name": "unit_tests", "status": "pass", "command": "python -m unittest discover -s tests"}],
        }

        markdown = run_full_preflight.render_markdown(report)

        self.assertIn("does not prove production RAG quality", markdown)
        self.assertIn("neural embedding performance", markdown)
        self.assertIn("| unit_tests | pass |", markdown)


if __name__ == "__main__":
    unittest.main()
