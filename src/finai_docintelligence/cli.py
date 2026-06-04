from __future__ import annotations

import argparse

from .analyzer import analyze
from .evaluation import evaluate_cases, write_eval_outputs
from .report import write_json, write_markdown


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
    eval_parser.add_argument("--out", default="reports/rag_eval_report.md", help="Markdown eval report path")
    eval_parser.add_argument("--json", default=None, help="Optional JSON eval artifact path")
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

    parser.error(f"Unknown command: {args.command}")
    return 2
