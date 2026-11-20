from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.repository_manifest import (
    MUTABLE_RELEASE_OUTPUTS,
    build_repository_manifest,
    render_markdown,
    verify_repository_manifest,
)


class RepositoryManifestTests(unittest.TestCase):
    def test_current_repository_manifest_excludes_mutable_release_outputs(self) -> None:
        manifest = build_repository_manifest(Path.cwd())
        paths = {item["path"] for item in manifest["files"]}

        self.assertFalse(paths & MUTABLE_RELEASE_OUTPUTS)
        self.assertIn("README.md", paths)
        self.assertIn("tools/run_full_preflight.py", paths)
        self.assertIn("reports/retrieval_comparison.md", paths)
        self.assertNotIn("reports/full_preflight_report.json", paths)

    def test_render_markdown_documents_publication_boundary(self) -> None:
        manifest = {
            "project": "financial-ai-doc-intelligence",
            "file_count": 1,
            "files": [{"path": "README.md", "role": "documentation", "bytes": 5, "sha256": "abc"}],
            "excluded_paths": sorted(MUTABLE_RELEASE_OUTPUTS),
            "limitations": ["File hashes prove publication package identity only."],
        }

        markdown = render_markdown(manifest)

        self.assertIn("# Repository Manifest", markdown)
        self.assertIn("post-publication", markdown)
        self.assertIn("mutable release-gate outputs", markdown)
        self.assertIn("File hashes prove publication package identity only.", markdown)

    def test_verify_repository_manifest_rejects_changed_file_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "README.md").write_text("first\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            manifest = build_repository_manifest(root)
            reports = root / "reports"
            reports.mkdir()
            manifest_path = reports / "repository_manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / "README.md").write_text("changed\n", encoding="utf-8")

            result = verify_repository_manifest(root, manifest_path)

        self.assertFalse(result["ok"])
        self.assertIn("sha256_mismatch:README.md", result["errors"])


if __name__ == "__main__":
    unittest.main()
