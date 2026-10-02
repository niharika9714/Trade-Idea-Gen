"""
Step 4B - Deterministic Reasoning Engine

Converts AnalysisResult into ReasoningResult.

This layer does NOT:
    - retrieve data
    - call external APIs
    - invent facts
    - generate unsupported claims

Every reasoning step must remain traceable to AnalysisResult
evidence IDs and citations.
"""

from __future__ import annotations

from typing import Any, Optional

from src.analysis.evidence_analysis import AnalysisResult
from src.analysis.reasoning_contract import (
    ReasoningInput,
    ReasoningResult,
    ReasoningStep,
    analysis_result_to_reasoning_input,
)


PRICE_METRICS = {
    "close_price",
    "share_price",
    "price",
}

PERFORMANCE_METRICS = {
    "return",
    "performance",
}

FUNDAMENTAL_METRICS = {
    "revenue",
    "net_income",
    "eps",
    "roe",
    "nim",
}

VALUATION_METRICS = {
    "pe",
    "pb",
    "target_price",
}


def _safe_date(value: Any) -> str:
    """
    Normalize a date-like value for deterministic comparison.
    """

    if value is None:
        return ""

    return str(value)


def _latest_fact(
    facts,
    entity: Optional[str] = None,
    metrics: Optional[set[str]] = None,
):
    """
    Return the latest dated fact matching the supplied filters.
    """

    candidates = []

    for fact in facts:
        if entity and fact.entity != entity:
            continue

        if metrics and fact.metric not in metrics:
            continue

        candidates.append(fact)

    if not candidates:
        return None

    candidates.sort(
        key=lambda fact: _safe_date(
            getattr(fact, "date", None)
        ),
        reverse=True,
    )

    return candidates[0]


def _facts_for_entity(
    facts,
    entity: str,
):
    return [
        fact
        for fact in facts
        if fact.entity == entity
    ]


def build_reasoning(
    query: str,
    analysis_result: AnalysisResult,
    query_intent=None,
) -> ReasoningResult:
    """
    Build a traceable reasoning result from AnalysisResult.

    The current implementation is deterministic. A future LLM can
    replace or enrich this stage, but it must continue to reference
    the same evidence IDs and citations.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError(
            "query must not be empty."
        )

    if analysis_result is None:
        raise ValueError(
            "analysis_result is required."
        )

    reasoning_input: ReasoningInput = (
        analysis_result_to_reasoning_input(
            query=query,
            analysis_result=analysis_result,
        )
    )

    result = ReasoningResult(
        query=query,
    )

    result.metadata["analysis_entities"] = list(
        reasoning_input.entities
    )

    result.metadata["analysis_fact_count"] = len(
        reasoning_input.facts
    )

    result.metadata["analysis_derived_metric_count"] = len(
        reasoning_input.derived_metrics
    )

    facts = list(
        analysis_result.facts
    )

    derived_metrics = list(
        analysis_result.derived_metrics
    )

    entities = list(
        analysis_result.entities
    )

    # ---------------------------------------------------------
    # No evidence
    # ---------------------------------------------------------

    if not facts and not derived_metrics:
        result.add_limitation(
            "No analyzable evidence was retrieved for the query."
        )

        return result

    # ---------------------------------------------------------
    # Price / share-price reasoning
    # ---------------------------------------------------------

    price_intent = False

    if query_intent is not None:
        metrics = set(
            getattr(
                query_intent,
                "metrics",
                [],
            )
            or []
        )

        intents = set(
            getattr(
                query_intent,
                "intents",
                [],
            )
            or []
        )

        price_intent = bool(
            metrics.intersection(
                {
                    "share_price",
                    "price",
                }
            )
            or "price" in intents
        )

    if price_intent:
        for entity in entities:
            fact = _latest_fact(
                facts,
                entity=entity,
                metrics=PRICE_METRICS,
            )

            if fact is None:
                continue

            result.add_step(
                ReasoningStep(
                    step_id=(
                        f"price-{entity}"
                    ),
                    description=(
                        "Identify the latest available "
                        "share-price observation for the entity."
                    ),
                    input_evidence_ids=list(
                        fact.evidence_ids
                    ),
                    input_citations=list(
                        fact.citations
                    ),
                    derived_from=[
                        fact.metric,
                        fact.date,
                    ],
                    conclusion=(
                        f"{entity} latest available "
                        f"share price is {fact.value}"
                        f"{(' ' + fact.unit) if fact.unit else ''}"
                        f" on {fact.date}."
                    ),
                    confidence=1.0,
                    metadata={
                        "entity": entity,
                        "metric": fact.metric,
                        "date": fact.date,
                    },
                )
            )

    # ---------------------------------------------------------
    # Derived metrics
    # ---------------------------------------------------------

    for metric in derived_metrics:
        result.add_step(
            ReasoningStep(
                step_id=(
                    f"derived-{metric.entity}-"
                    f"{metric.metric}"
                ),
                description=(
                    "Use the derived metric calculated "
                    "from retrieved source evidence."
                ),
                input_evidence_ids=list(
                    metric.input_evidence_ids
                ),
                input_citations=list(
                    metric.input_citations
                ),
                derived_from=[
                    metric.calculation
                ],
                conclusion=(
                    f"{metric.entity} {metric.metric} "
                    f"is {metric.value}"
                    f"{(' ' + metric.unit) if metric.unit else ''}."
                ),
                confidence=1.0,
                metadata={
                    "calculation": metric.calculation,
                },
            )
        )

    # ---------------------------------------------------------
    # Fundamental reasoning
    # ---------------------------------------------------------

    fundamental_intent = False

    if query_intent is not None:
        intents = set(
            getattr(
                query_intent,
                "intents",
                [],
            )
            or []
        )

        fundamental_intent = (
            "fundamentals" in intents
        )

    if fundamental_intent:
        for entity in entities:
            entity_facts = _facts_for_entity(
                facts,
                entity,
            )

            selected = [
                fact
                for fact in entity_facts
                if fact.metric in FUNDAMENTAL_METRICS
            ]

            for fact in selected:
                result.add_step(
                    ReasoningStep(
                        step_id=(
                            f"fundamental-{entity}-"
                            f"{fact.metric}-"
                            f"{fact.date}"
                        ),
                        description=(
                            "Identify the reported "
                            f"{fact.metric} value."
                        ),
                        input_evidence_ids=list(
                            fact.evidence_ids
                        ),
                        input_citations=list(
                            fact.citations
                        ),
                        derived_from=[
                            fact.metric,
                            fact.date,
                        ],
                        conclusion=(
                            f"{entity} {fact.metric} "
                            f"is {fact.value}"
                            f"{(' ' + fact.unit) if fact.unit else ''}"
                            f" for {fact.date}."
                        ),
                        confidence=1.0,
                    )
                )

    # ---------------------------------------------------------
    # Fallback factual reasoning
    # ---------------------------------------------------------

    if not result.reasoning_steps:
        for fact in facts[:10]:
            result.add_step(
                ReasoningStep(
                    step_id=(
                        f"fact-{fact.entity}-"
                        f"{fact.metric}-"
                        f"{fact.date}"
                    ),
                    description=(
                        "Report a retrieved factual observation."
                    ),
                    input_evidence_ids=list(
                        fact.evidence_ids
                    ),
                    input_citations=list(
                        fact.citations
                    ),
                    derived_from=[
                        fact.metric,
                        fact.date,
                    ],
                    conclusion=(
                        f"{fact.entity} {fact.metric} "
                        f"is {fact.value}"
                        f"{(' ' + fact.unit) if fact.unit else ''}"
                        f"{(' on ' + fact.date) if fact.date else ''}."
                    ),
                    confidence=1.0,
                )
            )

    # ---------------------------------------------------------
    # Supporting evidence
    # ---------------------------------------------------------

    for step in result.reasoning_steps:
        for evidence_id in step.input_evidence_ids:
            if evidence_id not in result.supporting_evidence_ids:
                result.supporting_evidence_ids.append(
                    evidence_id
                )

        for citation in step.input_citations:
            if citation not in result.supporting_citations:
                result.supporting_citations.append(
                    citation
                )

    return result