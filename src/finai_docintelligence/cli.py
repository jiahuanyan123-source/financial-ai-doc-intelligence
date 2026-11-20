from __future__ import annotations

import argparse

from .analyzer import analyze
from .embedding_retrieval import embed_texts_with_hashing
from .embedding_sensitivity import (
    evaluate_embedding_dimension_sensitivity,
    write_embedding_sensitivity_outputs,
)
from .evaluation import evaluate_cases, write_eval_outputs
from .report import write_json, write_markdown


def _parse_dimensions(value: str) -> tuple[int, ...]:
    parts = tuple(part.strip() for part in value.split(",") if part.strip())
    if not parts:
        raise argparse.ArgumentTypeError("Provide at least one dimension.")
    try:
        dimensions = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Dimensions must be comma-separated integers.") from exc
    if any(dimension <= 0 for dimension in dimensions):
        raise argparse.ArgumentTypeError("Dimensions must be positive integers.")
    return dimensions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Financial AI document intelligence baseline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze an issuer credit note")
    analyze_parser.add_argument("input", help="Path to a .txt or .md issuer note")
    analyze_parser.add_argument("--out", default="reports/report.md", help="Markdown report path")
    analyze_parser.add_argument("--json", default=None, help="Optional JSON artifact path")

    eval_parser = subparsers.add_parser("eval-rag", help="Run deterministic citation retrieval eval")
    eval_parser.add_argument("cases", help="Path to RAG eval case JSON")
    eval_parser.add_argument("--top-k", type=int, default=5, help="Number of source lines to retrieve per question")
    eval_parser.add_argument(
        "--retriever",
        choices=("source-prior", "hashing-embedding"),
        default="source-prior",
        help="Retrieval mode for the eval.",
    )
    eval_parser.add_argument(
        "--embedding-dimensions",
        type=int,
        default=128,
        help="Dimensions for the deterministic local hashing embedding backend.",
    )
    eval_parser.add_argument("--out", default="reports/rag_eval_report.md", help="Markdown eval report path")
    eval_parser.add_argument("--json", default=None, help="Optional JSON eval artifact path")

    sensitivity_parser = subparsers.add_parser(
        "embedding-sensitivity",
        help="Run deterministic hashing embedding dimension sensitivity eval",
    )
    sensitivity_parser.add_argument("cases", help="Path to RAG eval case JSON")
    sensitivity_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of source lines to retrieve per question",
    )
    sensitivity_parser.add_argument(
        "--dimensions",
        type=_parse_dimensions,
        default=(32, 64, 128, 256),
        help="Comma-separated hashing embedding dimensions to compare.",
    )
    sensitivity_parser.add_argument(
        "--out",
        default="reports/embedding_dimension_sensitivity.md",
        help="Markdown sensitivity report path",
    )
    sensitivity_parser.add_argument("--json", default=None, help="Optional JSON sensitivity artifact path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        result = analyze(args.input)
        write_markdown(result, args.out)
        if args.json:
            write_json(result, args.json)
        print(f"Wrote Markdown report to {args.out}")
        if args.json:
            print(f"Wrote JSON artifact to {args.json}")
        return 0

    if args.command == "eval-rag":
        if args.retriever == "hashing-embedding":
            report = evaluate_cases(
                args.cases,
                top_k=args.top_k,
                retriever="embedding",
                embed_texts=lambda texts: embed_texts_with_hashing(
                    texts,
                    dimensions=args.embedding_dimensions,
                ),
            )
        else:
            report = evaluate_cases(args.cases, top_k=args.top_k)
        write_eval_outputs(report, args.out, args.json)
        print(f"Wrote RAG eval report to {args.out}")
        if args.json:
            print(f"Wrote RAG eval JSON artifact to {args.json}")
        print(
            "Summary: "
            f"line_recall={report.average_line_recall:.2%}, "
            f"term_coverage={report.average_term_coverage:.2%}, "
            f"source_hit={report.average_source_hit:.2%}, "
            f"distractor_leak={report.average_distractor_leak_rate:.2%}, "
            f"pass_rate={report.pass_rate:.2%}"
        )
        return 0

    if args.command == "embedding-sensitivity":
        report = evaluate_embedding_dimension_sensitivity(
            args.cases,
            dimensions=args.dimensions,
            top_k=args.top_k,
        )
        write_embedding_sensitivity_outputs(report, args.out, args.json)
        print(f"Wrote embedding sensitivity report to {args.out}")
        if args.json:
            print(f"Wrote embedding sensitivity JSON artifact to {args.json}")
        best = ", ".join(str(dimension) for dimension in report.best_dimensions)
        worst = ", ".join(str(dimension) for dimension in report.worst_dimensions)
        print(f"Summary: best_dimensions={best}, worst_dimensions={worst}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
