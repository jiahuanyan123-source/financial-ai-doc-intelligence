from __future__ import annotations

import math
from hashlib import sha256
from typing import Callable, Sequence

from .analyzer import read_source
from .model import SourceLine
from .retrieval import tokenize
from .retrieval import RetrievedLine


EmbeddingFunction = Callable[[Sequence[str]], Sequence[Sequence[float]]]


class EmbeddingRetrieverUnavailable(RuntimeError):
    """Raised when embedding retrieval is selected without an embedding backend."""


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimension.")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)


def embed_texts_with_hashing(texts: Sequence[str], dimensions: int = 128) -> list[list[float]]:
    """Create deterministic lexical hashing vectors without external model calls.

    This is a local comparison backend, not a semantic embedding model.
    """
    if dimensions <= 0:
        raise ValueError("Embedding dimensions must be positive.")

    vectors: list[list[float]] = []
    for text in texts:
        vector = [0.0] * dimensions
        for token in tokenize(text):
            digest = sha256(token.encode("utf-8")).hexdigest()
            bucket = int(digest[:8], 16) % dimensions
            vector[bucket] += 1.0
        vectors.append(vector)
    return vectors


def retrieve_lines_from_sources_with_embeddings(
    sources: Sequence[tuple[str, str]],
    query: str,
    top_k: int = 5,
    context_window: int = 1,
    embed_texts: EmbeddingFunction | None = None,
) -> list[RetrievedLine]:
    if embed_texts is None:
        raise EmbeddingRetrieverUnavailable(
            "Embedding retrieval requires an explicit local embedding function; "
            "the deterministic source-prior retriever remains the default."
        )

    candidates: list[tuple[str, SourceLine]] = []
    line_lookup: dict[tuple[str, int], SourceLine] = {}
    for source_label, source_path in sources:
        for line in read_source(source_path):
            line_lookup[(source_label, line.number)] = line
            if line.text.strip():
                candidates.append((source_label, line))

    candidate_texts = [
        f"{source_label.replace('/', ' ').replace('_', ' ')}\n{line.text}"
        for source_label, line in candidates
    ]
    vectors = list(embed_texts([query, *candidate_texts]))
    if len(vectors) != len(candidates) + 1:
        raise ValueError("Embedding function must return one vector per input text.")

    query_vector = vectors[0]
    scored_by_line: dict[tuple[str, int], RetrievedLine] = {}
    for (source_label, line), vector in zip(candidates, vectors[1:]):
        score = cosine_similarity(query_vector, vector)
        if score > 0:
            scored_by_line[(source_label, line.number)] = RetrievedLine(source_label, line.number, line.text, score)

    for seed in list(scored_by_line.values()):
        for offset in range(-context_window, context_window + 1):
            if offset == 0:
                continue
            neighbor = line_lookup.get((seed.source, seed.line_number + offset))
            if neighbor is None or not neighbor.text.strip():
                continue
            context_score = seed.score * 0.8
            key = (seed.source, neighbor.number)
            current = scored_by_line.get(key)
            if current is None or context_score > current.score:
                scored_by_line[key] = RetrievedLine(seed.source, neighbor.number, neighbor.text, context_score)

    return sorted(scored_by_line.values(), key=lambda item: (-item.score, item.source, item.line_number))[:top_k]
