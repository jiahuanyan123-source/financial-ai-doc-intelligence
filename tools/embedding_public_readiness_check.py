from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_DIMENSIONS = {32, 64, 128, 256}
SENSITIVITY_CAVEATS = (
    "not a neural embedding model",
    "fixture-specific",
    "does not prove answer quality",
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": detail})


def evaluate_public_embedding_readiness(root: Path) -> dict[str, Any]:
    reports_dir = root / "reports"
    comparison_md = reports_dir / "retrieval_comparison.md"
    sensitivity_md = reports_dir / "embedding_dimension_sensitivity.md"
    sensitivity_json = reports_dir / "embedding_dimension_sensitivity.json"
    embedding_json = reports_dir / "embedding_rag_eval_report.json"
    checks: list[dict[str, Any]] = []

    required_files = (comparison_md, sensitivity_md, sensitivity_json, embedding_json)
    for path in required_files:
        _add_check(checks, f"file_exists:{path.relative_to(root)}", path.exists(), "required embedding evidence file")
    if not all(path.exists() for path in required_files):
        return _finalize(root, checks)

    comparison_text = comparison_md.read_text(encoding="utf-8").lower()
    normalized_comparison_text = " ".join(comparison_text.split())
    sensitivity_text = sensitivity_md.read_text(encoding="utf-8").lower()
    sensitivity = _load_json(sensitivity_json)
    embedding = _load_json(embedding_json)

    _add_check(
        checks,
        "comparison_caveat:not_neural",
        "not a neural embedding model" in comparison_text or "not a neural embedding benchmark" in comparison_text,
        "retrieval comparison must not frame hashing as neural embedding quality",
    )
    _add_check(
        checks,
        "comparison_caveat:dimension_sensitive",
        "dimension-sensitive" in comparison_text or "not stable across all dimensions" in comparison_text,
        "retrieval comparison must show that the hashing result depends on dimension choice",
    )
    _add_check(
        checks,
        "comparison_caveat:no_semantic_quality_claim",
        "robust semantic retrieval claim" in normalized_comparison_text
        or "too small to prove semantic retrieval quality" in normalized_comparison_text
        or "should not be presented as robust semantic retrieval quality" in normalized_comparison_text,
        "retrieval comparison must avoid promoting the toy result as semantic retrieval quality",
    )
    for phrase in SENSITIVITY_CAVEATS:
        _add_check(
            checks,
            f"sensitivity_caveat:{phrase}",
            phrase in sensitivity_text,
            "dimension sensitivity report must keep limitations visible",
        )

    results = sensitivity.get("results")
    dimensions = {
        int(item.get("dimensions"))
        for item in results
        if isinstance(item, dict) and isinstance(item.get("dimensions"), int)
    } if isinstance(results, list) else set()
    _add_check(
        checks,
        "sensitivity_dimensions",
        REQUIRED_DIMENSIONS.issubset(dimensions),
        f"observed dimensions: {sorted(dimensions)}",
    )

    embedding_pass_rate = embedding.get("pass_rate")
    pass_rates = {
        int(item.get("dimensions")): float(item.get("pass_rate"))
        for item in results
        if isinstance(item, dict)
        and isinstance(item.get("dimensions"), int)
        and isinstance(item.get("pass_rate"), (int, float))
    } if isinstance(results, list) else {}
    has_weaker_dimension = (
        isinstance(embedding_pass_rate, (int, float))
        and any(rate < float(embedding_pass_rate) for rate in pass_rates.values())
    )
    _add_check(
        checks,
        "dimension_dependence_visible",
        has_weaker_dimension,
        f"embedding pass_rate={embedding_pass_rate}; sensitivity pass rates={pass_rates}",
    )

    worst_dimensions = set(sensitivity.get("worst_dimensions", []))
    _add_check(
        checks,
        "failed_dimensions_visible",
        {32, 64}.issubset(worst_dimensions),
        f"worst_dimensions={sorted(worst_dimensions)}",
    )

    leak_rates = {
        int(item.get("dimensions")): float(item.get("average_distractor_leak_rate"))
        for item in results
        if isinstance(item, dict)
        and isinstance(item.get("dimensions"), int)
        and isinstance(item.get("average_distractor_leak_rate"), (int, float))
    } if isinstance(results, list) else {}
    _add_check(
        checks,
        "non_128_leak_visible",
        any(dimension != 128 and rate > 0 for dimension, rate in leak_rates.items()),
        f"distractor leak rates={leak_rates}",
    )

    _add_check(
        checks,
        "embedding_not_promoted_to_production",
        "production rag readiness" in sensitivity_text and "does not prove" in sensitivity_text,
        "report must explicitly avoid production-readiness claims",
    )
    return _finalize(root, checks)


def _finalize(root: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [check for check in checks if check["status"] != "pass"]
    return {
        "status": "pass" if not failures else "fail",
        "repository": "financial-ai-doc-intelligence",
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "summary": (
            "Local hashing embedding evidence is bounded by sensitivity caveats."
            if not failures
            else "Embedding evidence is missing required public-readiness caveats."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Embedding Public Readiness Check",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['check_count']}",
        f"Failures: {report['failure_count']}",
        "",
        report["summary"],
        "",
        "This gate does not validate real neural embedding quality. It only checks",
        "that the deterministic local hashing comparison keeps its limitations visible",
        "before the result is copied into public portfolio language.",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {check['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether local embedding comparison evidence is public-ready.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--json", default="reports/embedding_public_readiness_report.json", help="JSON output path.")
    parser.add_argument("--markdown", default="reports/embedding_public_readiness_report.md", help="Markdown output path.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = evaluate_public_embedding_readiness(root)

    json_path = root / args.json
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    markdown_path = root / args.markdown
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")

    if report["status"] == "pass":
        print("EMBEDDING_PUBLIC_READINESS_OK")
        return 0
    print("EMBEDDING_PUBLIC_READINESS_FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
