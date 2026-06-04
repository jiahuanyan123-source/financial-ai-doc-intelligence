from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceLine:
    number: int
    text: str


@dataclass(frozen=True)
class ExtractedField:
    name: str
    value: Any
    unit: str | None = None
    source_line: int | None = None


@dataclass(frozen=True)
class Metric:
    name: str
    value: float
    unit: str
    formula: str


@dataclass(frozen=True)
class RiskFlag:
    severity: str
    category: str
    message: str
    source_lines: tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AnalysisResult:
    source_path: str
    fields: dict[str, ExtractedField]
    metrics: dict[str, Metric]
    risks: list[RiskFlag]
    analyst_questions: list[str]

