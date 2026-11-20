from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PreflightStep:
    name: str
    command: tuple[str, ...]


def build_preflight_steps() -> list[PreflightStep]:
    return [
        PreflightStep("unit_tests", (sys.executable, "-m", "unittest", "discover", "-s", "tests")),
        PreflightStep(
            "sample_analysis_report",
            (
                sys.executable,
                "-m",
                "finai_docintelligence",
                "analyze",
                "examples/sample_issuer_credit_note.md",
                "--out",
                "reports/sample_report.md",
                "--json",
                "reports/sample_report.json",
            ),
        ),
        PreflightStep(
            "single_document_rag_eval",
            (
                sys.executable,
                "-m",
                "finai_docintelligence",
                "eval-rag",
                "examples/rag_eval_cases.json",
                "--out",
                "reports/rag_eval_report.md",
                "--json",
                "reports/rag_eval_report.json",
            ),
        ),
        PreflightStep(
            "multi_document_rag_eval",
            (
                sys.executable,
                "-m",
                "finai_docintelligence",
                "eval-rag",
                "examples/multi_doc_rag_eval_cases.json",
                "--out",
                "reports/multi_doc_rag_eval_report.md",
                "--json",
                "reports/multi_doc_rag_eval_report.json",
            ),
        ),
        PreflightStep(
            "hashing_embedding_eval",
            (
                sys.executable,
                "-m",
                "finai_docintelligence",
                "eval-rag",
                "examples/multi_doc_rag_eval_cases.json",
                "--retriever",
                "hashing-embedding",
                "--embedding-dimensions",
                "128",
                "--out",
                "reports/embedding_rag_eval_report.md",
                "--json",
                "reports/embedding_rag_eval_report.json",
            ),
        ),
        PreflightStep(
            "embedding_dimension_sensitivity",
            (
                sys.executable,
                "-m",
                "finai_docintelligence",
                "embedding-sensitivity",
                "examples/multi_doc_rag_eval_cases.json",
                "--dimensions",
                "32,64,128,256",
                "--out",
                "reports/embedding_dimension_sensitivity.md",
                "--json",
                "reports/embedding_dimension_sensitivity.json",
            ),
        ),
        PreflightStep(
            "embedding_public_readiness",
            (
                sys.executable,
                "tools/embedding_public_readiness_check.py",
                "--json",
                "reports/embedding_public_readiness_report.json",
                "--markdown",
                "reports/embedding_public_readiness_report.md",
            ),
        ),
        PreflightStep(
            "repository_manifest",
            (
                sys.executable,
                "tools/repository_manifest.py",
                "--json",
                "reports/repository_manifest.json",
                "--markdown",
                "reports/repository_manifest.md",
            ),
        ),
        PreflightStep(
            "repository_manifest_verify",
            (
                sys.executable,
                "tools/repository_manifest.py",
                "--verify",
                "--json",
                "reports/repository_manifest.json",
            ),
        ),
    ]


def _display_command(command: tuple[str, ...]) -> str:
    normalized = ("python", *command[1:]) if command and Path(command[0]).name.startswith("python") else command
    return " ".join(normalized)


def _run_step(root: Path, step: PreflightStep) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        step.command,
        cwd=root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output_lines = result.stdout.strip().splitlines()
    check: dict[str, Any] = {
        "name": step.name,
        "status": "pass" if result.returncode == 0 else "fail",
        "return_code": result.returncode,
        "command": _display_command(step.command),
    }
    if result.returncode != 0:
        check["output_tail"] = output_lines[-12:]
    return check


def run_full_preflight(root: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for step in build_preflight_steps():
        check = _run_step(root, step)
        checks.append(check)
        if check["status"] != "pass":
            break

    failures = [check for check in checks if check["status"] != "pass"]
    return {
        "status": "pass" if not failures else "fail",
        "repository": "financial-ai-doc-intelligence",
        "generated_at_utc": "not_recorded_for_deterministic_report",
        "step_count": len(checks),
        "expected_step_count": len(build_preflight_steps()),
        "failure_count": len(failures),
        "checks": checks,
        "summary": (
            "All local Financial RAG release checks passed."
            if not failures
            else "Financial RAG preflight stopped at the first failing check."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Local Preflight Report",
        "",
        f"Status: `{report['status']}`",
        f"Repository: `{report['repository']}`",
        f"Generated UTC: `{report['generated_at_utc']}`",
        f"Steps: {report['step_count']} / {report['expected_step_count']}",
        f"Failures: {report['failure_count']}",
        "",
        report["summary"],
        "",
        "This report is a local publication gate for the deterministic Financial RAG",
        "baseline. It does not prove production RAG quality, credit judgment quality,",
        "or neural embedding performance.",
        "",
        "## Checks",
        "",
        "| Step | Status | Command |",
        "| --- | --- | --- |",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | `{check['command']}` |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full local Financial RAG preflight.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--json", default="reports/full_preflight_report.json", help="JSON output path.")
    parser.add_argument("--markdown", default="reports/full_preflight_report.md", help="Markdown output path.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = run_full_preflight(root)

    json_path = root / args.json
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    markdown_path = root / args.markdown
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")

    if report["status"] == "pass":
        print("FINANCIAL_RAG_PREFLIGHT_OK")
        return 0
    print("FINANCIAL_RAG_PREFLIGHT_FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
