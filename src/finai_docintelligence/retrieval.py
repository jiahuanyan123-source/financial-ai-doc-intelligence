from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .analyzer import read_source
from .model import SourceLine


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "does",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "where",
    "which",
    "with",
}


@dataclass(frozen=True)
class RetrievedLine:
    source: str
    line_number: int
    text: str
    score: float


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOP_WORDS}


def score_line(query_tokens: set[str], line: SourceLine) -> float:
    line_tokens = tokenize(line.text)
    if not query_tokens or not line_tokens:
        return 0.0
    overlap = query_tokens & line_tokens
    return len(overlap) / len(query_tokens)


def score_source_prior(query_tokens: set[str], source_label: str) -> float:
    source_tokens = tokenize(source_label)
    if not query_tokens or not source_tokens:
        return 0.0
    overlap = query_tokens & source_tokens
    return len(overlap) / len(query_tokens)


def retrieve_lines(
    source_path: str,
    query: str,
    top_k: int = 5,
    context_window: int = 1,
    source_label: str | None = None,
) -> list[RetrievedLine]:
    label = source_label or Path(source_path).name
    query_tokens = tokenize(query)
    lines = read_source(source_path)
    scored_by_line: dict[int, RetrievedLine] = {}
    for line in lines:
        score = score_line(query_tokens, line)
        if score > 0:
            scored_by_line[line.number] = RetrievedLine(label, line.number, line.text, score)

    line_lookup = {line.number: line for line in lines}
    for seed in list(scored_by_line.values()):
        for offset in range(-context_window, context_window + 1):
            if offset == 0:
                continue
            neighbor = line_lookup.get(seed.line_number + offset)
            if neighbor is None or not neighbor.text.strip():
                continue
            context_score = seed.score * 0.8
            current = scored_by_line.get(neighbor.number)
            if current is None or context_score > current.score:
                scored_by_line[neighbor.number] = RetrievedLine(label, neighbor.number, neighbor.text, context_score)

    return sorted(scored_by_line.values(), key=lambda item: (-item.score, item.line_number))[:top_k]


def retrieve_lines_from_sources(
    sources: Sequence[tuple[str, str]],
    query: str,
    top_k: int = 5,
    context_window: int = 1,
) -> list[RetrievedLine]:
    retrieved: list[RetrievedLine] = []
    query_tokens = tokenize(query)
    for source_label, source_path in sources:
        source_prior = score_source_prior(query_tokens, source_label)
        source_results = retrieve_lines(
            source_path,
            query,
            top_k=top_k,
            context_window=context_window,
            source_label=source_label,
        )
        retrieved.extend(
            RetrievedLine(item.source, item.line_number, item.text, item.score + source_prior)
            for item in source_results
        )
    return sorted(retrieved, key=lambda item: (-item.score, item.source, item.line_number))[:top_k]
