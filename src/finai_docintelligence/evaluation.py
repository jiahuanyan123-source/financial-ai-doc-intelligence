from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .retrieval import RetrievedLine, retrieve_lines, retrieve_lines_from_sources


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    source_path: str
    source_label: str
    question: str
    expected_lines: tuple[int, ...]
    expected_terms: tuple[str, ...]
    candidate_sources: tuple[tuple[str, str], ...]
    forbidden_sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvalCaseResult:
    case_id: str
    question: str
    source: str
    expected_lines: tuple[int, ...]
    retrieved_lines: tuple[RetrievedLine, ...]
    line_recall: float
    term_coverage: float
    source_hit: float
    distractor_leak_rate: float
    passed: bool


@dataclass(frozen=True)
class EvalReport:
    cases: tuple[EvalCaseResult, ...]
    average_line_recall: float
    average_term_coverage: float
    average_source_hit: float
    average_distractor_leak_rate: float
    pass_rate: float


def load_cases(path: str | Path) -> list[EvalCase]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    base_dir = source.parent
    document_sources: tuple[tuple[str, str], ...] = tuple(
        (item["path"], str((base_dir / item["path"]).resolve())) for item in payload.get("documents", [])
    )
    cases: list[EvalCase] = []
    for item in payload["cases"]:
        source_path = str((base_dir / item["source"]).resolve())
        candidate_sources = document_sources or ((item["source"], source_path),)
        cases.append(
            EvalCase(
                case_id=item["id"],
                source_path=source_path,
                source_label=item["source"],
                question=item["question"],
                expected_lines=tuple(int(line) for line in item["expected_lines"]),
                expected_terms=tuple(str(term) for term in item["expected_terms"]),
                candidate_sources=candidate_sources,
                forbidden_sources=tuple(str(source) for source in item.get("forbidden_sources", [])),
            )
        )
    return cases


def evaluate_case(case: EvalCase, top_k: int = 5) -> EvalCaseResult:
    if len(case.candidate_sources) > 1:
        retrieved = tuple(retrieve_lines_from_sources(case.candidate_sources, case.question, top_k=top_k))
    else:
        retrieved = tuple(retrieve_lines(case.source_path, case.question, top_k=top_k, source_label=case.source_label))
    retrieved_line_numbers = {item.line_number for item in retrieved if item.source == case.source_label}
    expected_line_numbers = set(case.expected_lines)
    line_recall = len(expected_line_numbers & retrieved_line_numbers) / len(expected_line_numbers)

    retrieved_text = " ".join(item.text.lower() for item in retrieved)
    matched_terms = sum(1 for term in case.expected_terms if term.lower() in retrieved_text)
    term_coverage = matched_terms / len(case.expected_terms) if case.expected_terms else 1.0
    source_hit = 1.0 if any(item.source == case.source_label for item in retrieved) else 0.0
    forbidden = set(case.forbidden_sources)
    distractor_hits = sum(1 for item in retrieved if item.source in forbidden)
    distractor_leak_rate = distractor_hits / len(retrieved) if retrieved else 0.0
    passed = line_recall >= 1.0 and term_coverage >= 0.8 and source_hit >= 1.0 and distractor_leak_rate == 0.0

    return EvalCaseResult(
        case_id=case.case_id,
        question=case.question,
        source=case.source_label,
        expected_lines=case.expected_lines,
        retrieved_lines=retrieved,
        line_recall=line_recall,
        term_coverage=term_coverage,
        source_hit=source_hit,
        distractor_leak_rate=distractor_leak_rate,
        passed=passed,
    )


def evaluate_cases(path: str | Path, top_k: int = 5) -> EvalReport:
    results = tuple(evaluate_case(case, top_k=top_k) for case in load_cases(path))
    count = len(results)
    average_line_recall = sum(result.line_recall for result in results) / count if count else 0.0
    average_term_coverage = sum(result.term_coverage for result in results) / count if count else 0.0
    average_source_hit = sum(result.source_hit for result in results) / count if count else 0.0
    average_distractor_leak_rate = sum(result.distractor_leak_rate for result in results) / count if count else 0.0
    pass_rate = sum(1 for result in results if result.passed) / count if count else 0.0
    return EvalReport(
        cases=results,
        average_line_recall=average_line_recall,
        average_term_coverage=average_term_coverage,
        average_source_hit=average_source_hit,
        average_distractor_leak_rate=average_distractor_leak_rate,
        pass_rate=pass_rate,
    )


def render_eval_markdown(report: EvalReport) -> str:
    lines = [
        "# Financial RAG Eval Report",
        "",
        "This deterministic baseline scores whether retrieval returns the expected source lines.",
        "It is a citation-control test, not an LLM quality claim.",
        "",
        "## Summary",
        "",
        f"- Cases: {len(report.cases)}",
        f"- Average line recall@k: {report.average_line_recall:.2%}",
        f"- Average expected-term coverage@k: {report.average_term_coverage:.2%}",
        f"- Average source document hit@k: {report.average_source_hit:.2%}",
        f"- Average distractor leak rate@k: {report.average_distractor_leak_rate:.2%}",
        f"- Pass rate: {report.pass_rate:.2%}",
        "",
        "## Cases",
        "",
    ]

    for result in report.cases:
        status = "PASS" if result.passed else "FAIL"
        lines.extend(
            [
                f"### {result.case_id}: {status}",
                "",
                f"Question: {result.question}",
                "",
                f"- Expected lines: {', '.join(map(str, result.expected_lines))}",
                f"- Line recall@k: {result.line_recall:.2%}",
                f"- Expected-term coverage@k: {result.term_coverage:.2%}",
                f"- Source document hit@k: {result.source_hit:.2%}",
                f"- Distractor leak rate@k: {result.distractor_leak_rate:.2%}",
                "",
                "| Rank | Source | Line | Score | Text |",
                "| ---: | --- | ---: | ---: | --- |",
            ]
        )
        for rank, item in enumerate(result.retrieved_lines, start=1):
            lines.append(f"| {rank} | {item.source} | {item.line_number} | {item.score:.2f} | {item.text} |")
        lines.append("")

    lines.extend(
        [
            "## Limitations",
            "",
            "- This v0 uses token overlap with one-line neighbor expansion, not embeddings.",
            "- The sample documents are synthetic and public-safe.",
            "- Passing this eval does not prove answer quality; it only checks retrieval of expected evidence lines.",
            "",
        ]
    )
    return "\n".join(lines)


def write_eval_outputs(report: EvalReport, markdown_path: str | Path, json_path: str | Path | None = None) -> None:
    target = Path(markdown_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_eval_markdown(report), encoding="utf-8")
    if json_path:
        json_target = Path(json_path)
        json_target.parent.mkdir(parents=True, exist_ok=True)
        json_target.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
