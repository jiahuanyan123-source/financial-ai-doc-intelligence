from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from .embedding_retrieval import embed_texts_with_hashing
from .evaluation import evaluate_cases


@dataclass(frozen=True)
class EmbeddingDimensionResult:
    dimensions: int
    average_line_recall: float
    average_term_coverage: float
    average_source_hit: float
    average_distractor_leak_rate: float
    pass_rate: float


@dataclass(frozen=True)
class EmbeddingDimensionSensitivityReport:
    cases_path: str
    top_k: int
    dimensions: tuple[int, ...]
    results: tuple[EmbeddingDimensionResult, ...]
    best_dimensions: tuple[int, ...]
    worst_dimensions: tuple[int, ...]


def evaluate_embedding_dimension_sensitivity(
    path: str | Path,
    dimensions: Sequence[int] = (32, 64, 128, 256),
    top_k: int = 5,
) -> EmbeddingDimensionSensitivityReport:
    normalized_dimensions = tuple(int(dimension) for dimension in dimensions)
    if not normalized_dimensions:
        raise ValueError("At least one embedding dimension must be provided.")
    if any(dimension <= 0 for dimension in normalized_dimensions):
        raise ValueError("Embedding dimensions must be positive.")

    results: list[EmbeddingDimensionResult] = []
    for dimension in normalized_dimensions:
        report = evaluate_cases(
            path,
            top_k=top_k,
            retriever="embedding",
            embed_texts=lambda texts, dimension=dimension: embed_texts_with_hashing(
                texts,
                dimensions=dimension,
            ),
        )
        results.append(
            EmbeddingDimensionResult(
                dimensions=dimension,
                average_line_recall=report.average_line_recall,
                average_term_coverage=report.average_term_coverage,
                average_source_hit=report.average_source_hit,
                average_distractor_leak_rate=report.average_distractor_leak_rate,
                pass_rate=report.pass_rate,
            )
        )

    best_pass_rate = max(result.pass_rate for result in results)
    worst_pass_rate = min(result.pass_rate for result in results)
    return EmbeddingDimensionSensitivityReport(
        cases_path=str(path),
        top_k=top_k,
        dimensions=normalized_dimensions,
        results=tuple(results),
        best_dimensions=tuple(result.dimensions for result in results if result.pass_rate == best_pass_rate),
        worst_dimensions=tuple(result.dimensions for result in results if result.pass_rate == worst_pass_rate),
    )


def render_embedding_sensitivity_markdown(report: EmbeddingDimensionSensitivityReport) -> str:
    lines = [
        "# Embedding Dimension Sensitivity Report",
        "",
        "This report checks whether the deterministic local hashing-embedding result",
        "is stable across vector dimensions on the same public-safe multi-document",
        "fixture.",
        "",
        "## Evaluation Contract",
        "",
        f"- Eval file: `{report.cases_path}`",
        f"- Top-k: {report.top_k}",
        "- Retriever: deterministic local hashing embedding",
        "- External model/API calls: none",
        "",
        "## Results",
        "",
        "| Dimensions | Line recall@k | Term coverage@k | Source hit@k | Distractor leak@k | Pass rate |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for result in report.results:
        lines.append(
            "| "
            f"{result.dimensions} | "
            f"{result.average_line_recall:.2%} | "
            f"{result.average_term_coverage:.2%} | "
            f"{result.average_source_hit:.2%} | "
            f"{result.average_distractor_leak_rate:.2%} | "
            f"{result.pass_rate:.2%} |"
        )

    best = ", ".join(str(dimension) for dimension in report.best_dimensions)
    worst = ", ".join(str(dimension) for dimension in report.worst_dimensions)
    best_pass_rate = max(result.pass_rate for result in report.results)
    worst_pass_rate = min(result.pass_rate for result in report.results)
    lines.extend(
        [
            "",
            "## Finding",
            "",
            f"- Best pass rate: {best_pass_rate:.2%} at dimensions {best}.",
            f"- Worst pass rate: {worst_pass_rate:.2%} at dimensions {worst}.",
            "- The 128-dimension result should be treated as fixture-specific until",
            "  it is repeated with a real local neural embedding backend and broader",
            "  issuer-document cases.",
            "",
            "## Limitations",
            "",
            "- This is a deterministic lexical hashing backend, not a neural embedding model.",
            "- The fixture is synthetic and intentionally small.",
            "- Passing this report does not prove answer quality or production RAG readiness.",
            "",
        ]
    )
    return "\n".join(lines)


def write_embedding_sensitivity_outputs(
    report: EmbeddingDimensionSensitivityReport,
    markdown_path: str | Path,
    json_path: str | Path | None = None,
) -> None:
    target = Path(markdown_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_embedding_sensitivity_markdown(report), encoding="utf-8")
    if json_path:
        json_target = Path(json_path)
        json_target.parent.mkdir(parents=True, exist_ok=True)
        json_target.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
