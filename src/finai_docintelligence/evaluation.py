from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from .embedding_retrieval import EmbeddingFunction, retrieve_lines_from_sources_with_embeddings
from .retrieval import RetrievedLine, retrieve_lines, retrieve_lines_from_sources

RetrieverMode = Literal["source-prior", "embedding"]


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
    line_recall: float | None
    term_coverage: float | None
    source_hit: float | None
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
    retriever: str = "source-prior"


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


def evaluate_case(
    case: EvalCase,
    top_k: int = 5,
    retriever: RetrieverMode = "source-prior",
    embed_texts: EmbeddingFunction | None = None,
) -> EvalCaseResult:
    if retriever == "embedding":
        retrieved = tuple(
            retrieve_lines_from_sources_with_embeddings(
                case.candidate_sources,
                case.question,
                top_k=top_k,
                embed_texts=embed_texts,
            )
        )
    elif retriever == "source-prior" and len(case.candidate_sources) > 1:
        retrieved = tuple(retrieve_lines_from_sources(case.candidate_sources, case.question, top_k=top_k))
    elif retriever == "source-prior":
        retrieved = tuple(retrieve_lines(case.source_path, case.question, top_k=top_k, source_label=case.source_label))
    else:
        raise ValueError(f"Unknown retriever mode: {retriever}")
    retrieved_line_numbers = {item.line_number for item in retrieved if item.source == case.source_label}
    expected_line_numbers = set(case.expected_lines)
    line_recall = (
        len(expected_line_numbers & retrieved_line_numbers) / len(expected_line_numbers)
        if expected_line_numbers else None
    )

    retrieved_text = " ".join(item.text.lower() for item in retrieved)
    matched_terms = sum(1 for term in case.expected_terms if term.lower() in retrieved_text)
    term_coverage = matched_terms / len(case.expected_terms) if case.expected_terms else 1.0
    source_hit = 1.0 if any(item.source == case.source_label for item in retrieved) else 0.0
    forbidden = set(case.forbidden_sources)
    distractor_hits = sum(1 for item in retrieved if item.source in forbidden)
    distractor_leak_rate = distractor_hits / len(retrieved) if retrieved else 0.0
    if line_recall is None:
        term_coverage = source_hit = None
        passed = not retrieved
    else:
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


def evaluate_cases(
    path: str | Path,
    top_k: int = 5,
    retriever: RetrieverMode = "source-prior",
    embed_texts: EmbeddingFunction | None = None,
) -> EvalReport:
    results = tuple(
        evaluate_case(case, top_k=top_k, retriever=retriever, embed_texts=embed_texts) for case in load_cases(path)
    )
    count = len(results)
    average_line_recall = _mean(result.line_recall for result in results)
    average_term_coverage = _mean(result.term_coverage for result in results)
    average_source_hit = _mean(result.source_hit for result in results)
    average_distractor_leak_rate = sum(result.distractor_leak_rate for result in results) / count if count else 0.0
    pass_rate = sum(1 for result in results if result.passed) / count if count else 0.0
    return EvalReport(
        cases=results,
        average_line_recall=average_line_recall,
        average_term_coverage=average_term_coverage,
        average_source_hit=average_source_hit,
        average_distractor_leak_rate=average_distractor_leak_rate,
        pass_rate=pass_rate,
        retriever=retriever,
    )


def _mean(values: Iterable[float | None]) -> float:
    present = [value for value in values if value is not None]
    return sum(present) / len(present) if present else 0.0


def _percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2%}"


def render_eval_markdown(report: EvalReport) -> str:
    lines = [
        "# Financial RAG Eval Report",
        "",
        f"Retriever: `{report.retriever}`",
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
                f"- Expected lines: {', '.join(map(str, result.expected_lines)) or 'none; expect no retrieved evidence'}",
                f"- Line recall@k: {_percent(result.line_recall)}",
                f"- Expected-term coverage@k: {_percent(result.term_coverage)}",
                f"- Source document hit@k: {_percent(result.source_hit)}",
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
            _retriever_limitation(report.retriever),
            "- The sample documents are synthetic and public-safe.",
            "- Passing this eval does not prove answer quality; it only checks retrieval of expected evidence lines.",
            "",
        ]
    )
    return "\n".join(lines)


def _retriever_limitation(retriever: str) -> str:
    if retriever == "embedding":
        return (
            "- This embedding run uses a deterministic local hashing backend, "
            "not a neural embedding model or external API."
        )
    return "- This v0 uses token overlap with one-line neighbor expansion, not embeddings."


def write_eval_outputs(report: EvalReport, markdown_path: str | Path, json_path: str | Path | None = None) -> None:
    target = Path(markdown_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_eval_markdown(report), encoding="utf-8")
    if json_path:
        json_target = Path(json_path)
        json_target.parent.mkdir(parents=True, exist_ok=True)
        json_target.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
