from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


MUTABLE_RELEASE_OUTPUTS = {
    "reports/full_preflight_report.json",
    "reports/full_preflight_report.md",
    "reports/repository_manifest.json",
    "reports/repository_manifest.md",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify a deterministic tracked-file manifest.")
    parser.add_argument("--json", type=Path, default=Path("reports/repository_manifest.json"))
    parser.add_argument("--markdown", type=Path, default=Path("reports/repository_manifest.md"))
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify that the existing JSON manifest matches the current tracked-file set.",
    )
    args = parser.parse_args(argv)

    root = Path.cwd()
    if args.verify:
        result = verify_repository_manifest(root, args.json)
        if result["ok"]:
            print("REPOSITORY_MANIFEST_VERIFY_OK")
            return 0
        for error in result["errors"]:
            print(f"REPOSITORY_MANIFEST_VERIFY_FAIL: {error}", file=sys.stderr)
        return 1

    manifest = build_repository_manifest(root)
    _write_text(args.json, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _write_text(args.markdown, render_markdown(manifest))
    print("REPOSITORY_MANIFEST_OK")
    return 0


def verify_repository_manifest(root: Path, manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.is_file():
        return {"ok": False, "errors": [f"manifest_missing:{manifest_path.as_posix()}"]}
    try:
        expected = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "errors": [f"manifest_invalid_json:{exc.msg}"]}

    current = build_repository_manifest(root)
    errors: list[str] = []
    for key in ("manifest_version", "project", "file_count"):
        if expected.get(key) != current.get(key):
            errors.append(f"{key}_mismatch:{expected.get(key)}!={current.get(key)}")

    expected_files = {
        item.get("path"): item
        for item in expected.get("files", [])
        if isinstance(item, dict) and item.get("path")
    }
    current_files = {item["path"]: item for item in current["files"]}
    for path in sorted(set(expected_files) | set(current_files)):
        expected_item = expected_files.get(path)
        current_item = current_files.get(path)
        if expected_item is None:
            errors.append(f"unexpected_current_file:{path}")
            continue
        if current_item is None:
            errors.append(f"expected_file_missing_now:{path}")
            continue
        for key in ("bytes", "sha256", "role"):
            if expected_item.get(key) != current_item[key]:
                errors.append(f"{key}_mismatch:{path}")

    return {"ok": not errors, "errors": errors}


def build_repository_manifest(root: Path) -> dict[str, Any]:
    files = [_file_record(root, rel_path) for rel_path in _tracked_paths(root)]
    return {
        "manifest_version": 1,
        "project": "financial-ai-doc-intelligence",
        "file_count": len(files),
        "files": files,
        "excluded_paths": sorted(MUTABLE_RELEASE_OUTPUTS),
        "limitations": [
            "This manifest fingerprints tracked repository files only.",
            "The manifest excludes mutable release-gate outputs to avoid self-referential hashes.",
            "File hashes prove publication package identity only; they do not prove production RAG quality or credit judgment quality.",
        ],
    }


def render_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Repository Manifest",
        "",
        f"Project: `{manifest['project']}`",
        f"Tracked files fingerprinted: `{manifest['file_count']}`",
        "",
        "This manifest supports pre-publication and post-publication file-inventory",
        "checks when normal Git push is unavailable. It fingerprints tracked",
        "repository files and excludes mutable release-gate outputs that would",
        "otherwise change while the preflight is writing reports.",
        "",
        "## Files",
        "",
        "| Path | Role | Bytes | SHA256 |",
        "| --- | --- | ---: | --- |",
    ]
    for item in manifest["files"]:
        lines.append(f"| `{item['path']}` | `{item['role']}` | {item['bytes']} | `{item['sha256']}` |")

    lines.extend(["", "## Excluded Mutable Release-Gate Outputs", ""])
    for path in manifest["excluded_paths"]:
        lines.append(f"- `{path}`")

    lines.extend(["", "## Limitations", ""])
    for limitation in manifest["limitations"]:
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def _tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return sorted(
        path.strip().replace("\\", "/")
        for path in result.stdout.splitlines()
        if path.strip() and path.strip().replace("\\", "/") not in MUTABLE_RELEASE_OUTPUTS
    )


def _file_record(root: Path, rel_path: str) -> dict[str, Any]:
    content = (root / rel_path).read_bytes()
    return {
        "path": rel_path,
        "role": _role_for_path(rel_path),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _role_for_path(path: str) -> str:
    if path.startswith(".github/"):
        return "ci_workflow"
    if path.startswith("src/"):
        return "source_code"
    if path.startswith("tests/"):
        return "test_code"
    if path.startswith("tools/"):
        return "release_tooling"
    if path.startswith("docs/") or path == "README.md":
        return "documentation"
    if path.startswith("examples/"):
        return "example_input"
    if path.startswith("reports/"):
        return "evidence_report"
    return "project_file"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
