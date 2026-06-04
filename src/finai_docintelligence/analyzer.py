from __future__ import annotations

import re
from pathlib import Path

from .model import AnalysisResult, ExtractedField, Metric, RiskFlag, SourceLine


FIELD_PATTERNS = {
    "issuer": re.compile(r"^\s*issuer\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE),
    "rating": re.compile(r"^\s*rating\s*:\s*(?P<value>[A-Z]{1,3}[+-]?)\s*$", re.IGNORECASE),
    "industry": re.compile(r"^\s*industry\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE),
    "ownership": re.compile(r"^\s*ownership\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE),
}

NUMERIC_PATTERNS = {
    "revenue": re.compile(r"^\s*revenue\s*:\s*(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<unit>bn|mn|m|billion|million)?\s*$", re.IGNORECASE),
    "ebitda": re.compile(r"^\s*ebitda\s*:\s*(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<unit>bn|mn|m|billion|million)?\s*$", re.IGNORECASE),
    "total_debt": re.compile(r"^\s*total debt\s*:\s*(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<unit>bn|mn|m|billion|million)?\s*$", re.IGNORECASE),
    "short_term_debt": re.compile(r"^\s*short-term debt\s*:\s*(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<unit>bn|mn|m|billion|million)?\s*$", re.IGNORECASE),
    "cash": re.compile(r"^\s*cash\s*:\s*(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<unit>bn|mn|m|billion|million)?\s*$", re.IGNORECASE),
    "operating_cash_flow": re.compile(r"^\s*operating cash flow\s*:\s*(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<unit>bn|mn|m|billion|million)?\s*$", re.IGNORECASE),
    "capital_expenditure": re.compile(r"^\s*capital expenditure\s*:\s*(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<unit>bn|mn|m|billion|million)?\s*$", re.IGNORECASE),
    "interest_expense": re.compile(r"^\s*interest expense\s*:\s*(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<unit>bn|mn|m|billion|million)?\s*$", re.IGNORECASE),
}

QUALITATIVE_RISK_KEYWORDS = {
    "perpetual": ("medium", "Capital structure", "Perpetual debt appears in the financing structure."),
    "guarantee": ("medium", "Contingent liability", "Guarantee exposure appears in the document."),
    "guarantees": ("medium", "Contingent liability", "Guarantee exposure appears in the document."),
    "litigation": ("low", "Legal risk", "Litigation is mentioned and should be reviewed."),
    "negative": ("medium", "Cash flow", "Negative cash flow language appears in the document."),
}

NEGATION_TERMS = {"no", "not", "none", "without"}


def read_source(path: str | Path) -> list[SourceLine]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    return [SourceLine(number=i, text=line.rstrip()) for i, line in enumerate(text.splitlines(), start=1)]


def extract_fields(lines: list[SourceLine]) -> dict[str, ExtractedField]:
    fields: dict[str, ExtractedField] = {}
    for line in lines:
        for name, pattern in FIELD_PATTERNS.items():
            match = pattern.match(line.text)
            if match:
                fields[name] = ExtractedField(name=name, value=match.group("value"), source_line=line.number)
        for name, pattern in NUMERIC_PATTERNS.items():
            match = pattern.match(line.text)
            if match:
                unit = normalize_unit(match.group("unit"))
                fields[name] = ExtractedField(
                    name=name,
                    value=float(match.group("value")),
                    unit=unit,
                    source_line=line.number,
                )
    return fields


def normalize_unit(unit: str | None) -> str:
    if unit is None:
        return "unit"
    unit = unit.lower()
    if unit in {"bn", "billion"}:
        return "bn"
    if unit in {"mn", "m", "million"}:
        return "mn"
    return unit


def number(fields: dict[str, ExtractedField], name: str) -> float | None:
    field = fields.get(name)
    if field is None:
        return None
    if not isinstance(field.value, int | float):
        return None
    return float(field.value)


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def compute_metrics(fields: dict[str, ExtractedField]) -> dict[str, Metric]:
    revenue = number(fields, "revenue")
    ebitda = number(fields, "ebitda")
    total_debt = number(fields, "total_debt")
    short_term_debt = number(fields, "short_term_debt")
    cash = number(fields, "cash")
    operating_cash_flow = number(fields, "operating_cash_flow")
    capital_expenditure = number(fields, "capital_expenditure")
    interest_expense = number(fields, "interest_expense")

    metrics: dict[str, Metric] = {}
    add_metric(metrics, "debt_to_ebitda", safe_ratio(total_debt, ebitda), "x", "total debt / EBITDA")
    add_metric(metrics, "cash_to_short_term_debt", safe_ratio(cash, short_term_debt), "x", "cash / short-term debt")
    add_metric(metrics, "interest_coverage", safe_ratio(ebitda, interest_expense), "x", "EBITDA / interest expense")
    add_metric(metrics, "debt_to_revenue", safe_ratio(total_debt, revenue), "x", "total debt / revenue")
    if operating_cash_flow is not None and capital_expenditure is not None:
        metrics["free_cash_flow"] = Metric(
            name="free_cash_flow",
            value=operating_cash_flow - capital_expenditure,
            unit="bn",
            formula="operating cash flow - capital expenditure",
        )
    return metrics


def add_metric(metrics: dict[str, Metric], name: str, value: float | None, unit: str, formula: str) -> None:
    if value is None:
        return
    metrics[name] = Metric(name=name, value=value, unit=unit, formula=formula)


def detect_risks(
    fields: dict[str, ExtractedField],
    metrics: dict[str, Metric],
    lines: list[SourceLine],
) -> list[RiskFlag]:
    risks: list[RiskFlag] = []

    leverage = metrics.get("debt_to_ebitda")
    if leverage and leverage.value >= 8:
        risks.append(RiskFlag("high", "Leverage", f"Debt/EBITDA is very high at {leverage.value:.2f}x."))
    elif leverage and leverage.value >= 5:
        risks.append(RiskFlag("medium", "Leverage", f"Debt/EBITDA is elevated at {leverage.value:.2f}x."))

    liquidity = metrics.get("cash_to_short_term_debt")
    if liquidity and liquidity.value < 0.8:
        risks.append(RiskFlag("high", "Liquidity", f"Cash covers only {liquidity.value:.2f}x of short-term debt."))
    elif liquidity and liquidity.value < 1.2:
        risks.append(RiskFlag("medium", "Liquidity", f"Cash coverage of short-term debt is modest at {liquidity.value:.2f}x."))

    coverage = metrics.get("interest_coverage")
    if coverage and coverage.value < 2:
        risks.append(RiskFlag("high", "Debt service", f"Interest coverage is weak at {coverage.value:.2f}x."))
    elif coverage and coverage.value < 4:
        risks.append(RiskFlag("medium", "Debt service", f"Interest coverage is moderate at {coverage.value:.2f}x."))

    free_cash_flow = metrics.get("free_cash_flow")
    if free_cash_flow and free_cash_flow.value < 0:
        risks.append(RiskFlag("medium", "Cash flow", f"Free cash flow is negative at {free_cash_flow.value:.2f} bn."))

    for keyword, (severity, category, message) in QUALITATIVE_RISK_KEYWORDS.items():
        hit_lines = tuple(
            line.number
            for line in lines
            if re.search(rf"\b{re.escape(keyword)}\b", line.text, re.IGNORECASE)
            and not is_negated_keyword(line.text, keyword)
        )
        if hit_lines:
            risks.append(RiskFlag(severity, category, message, hit_lines))

    return dedupe_risks(risks)


def dedupe_risks(risks: list[RiskFlag]) -> list[RiskFlag]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[RiskFlag] = []
    for risk in risks:
        key = (risk.severity, risk.category, risk.message)
        if key not in seen:
            unique.append(risk)
            seen.add(key)
    return unique


def is_negated_keyword(text: str, keyword: str) -> bool:
    lower = text.lower()
    match = re.search(rf"\b{re.escape(keyword.lower())}\b", lower)
    if not match:
        return False
    prefix = lower[: match.start()]
    tokens = re.findall(r"\b[a-z]+\b", prefix)
    return any(token in NEGATION_TERMS for token in tokens[-5:])


def build_analyst_questions(result: AnalysisResult) -> list[str]:
    questions: list[str] = []
    if "cash_to_short_term_debt" in result.metrics and result.metrics["cash_to_short_term_debt"].value < 1.2:
        questions.append("What committed bank lines or refinancing arrangements cover upcoming short-term debt?")
    if "free_cash_flow" in result.metrics and result.metrics["free_cash_flow"].value < 0:
        questions.append("Which capex projects are discretionary, and what is the expected funding mix?")
    if any(r.category == "Contingent liability" for r in result.risks):
        questions.append("What is the size, beneficiary, and maturity profile of external guarantees?")
    if any(r.category == "Capital structure" for r in result.risks):
        questions.append("How should perpetual instruments be treated under the investor's internal leverage framework?")
    if not questions:
        questions.append("What are the key downside scenarios that could weaken the issuer's liquidity profile?")
    return questions


def analyze(path: str | Path) -> AnalysisResult:
    source_path = str(Path(path))
    lines = read_source(source_path)
    fields = extract_fields(lines)
    metrics = compute_metrics(fields)
    risks = detect_risks(fields, metrics, lines)
    partial = AnalysisResult(source_path=source_path, fields=fields, metrics=metrics, risks=risks, analyst_questions=[])
    return AnalysisResult(
        source_path=source_path,
        fields=fields,
        metrics=metrics,
        risks=risks,
        analyst_questions=build_analyst_questions(partial),
    )
