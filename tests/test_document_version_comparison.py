import json
from pathlib import Path
import unittest

from tools.compare_document_versions import compare_versions


class DocumentVersionComparisonTests(unittest.TestCase):
    def test_fixture_reports_each_change_with_source_text(self):
        fixture = Path(__file__).resolve().parents[1] / "examples" / "document_versions.json"
        versions = json.loads(fixture.read_text(encoding="utf-8"))
        changed, removed, added = compare_versions(versions["before"], versions["after"])
        self.assertEqual(changed, {
            "id": "response_window", "status": "changed",
            "before": "Respond within 3 business days.", "after": "Respond within 5 business days.",
        })
        self.assertEqual(removed["status"], "removed")
        self.assertIsNone(removed["after"])
        self.assertEqual(added["status"], "added")
        self.assertIsNone(added["before"])

    def test_whitespace_only_change_is_ignored(self):
        self.assertEqual(compare_versions(
            [{"id": "a", "text": "Business days"}],
            [{"id": "a", "text": " Business\n days "}],
        ), [])

    def test_duplicate_id_is_rejected(self):
        section = {"id": "a", "text": "Fictional clause."}
        with self.assertRaisesRegex(ValueError, "Duplicate section ID"):
            compare_versions([], [section, section])

    def test_invalid_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "array"):
            compare_versions([], {})
