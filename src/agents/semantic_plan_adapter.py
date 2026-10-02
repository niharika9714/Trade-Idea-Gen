from __future__ import annotations

from src.agents.agent_plan_schema import AgentPlan
from src.data_access.query_intent import QueryIntent
from src.data_access.temporal_grounding import (
    ground_temporal_expression,
)


def agent_plan_to_query_intent(
    plan: AgentPlan,
) -> QueryIntent:
    """
    Convert the semantic AgentPlan produced by Qwen into the
    canonical QueryIntent contract expected by deterministic
    retrieval and analytical layers.

    This adapter does not perform semantic entity recognition.
    Qwen remains responsible for understanding the query.
    """

    if plan is None:
        raise ValueError(
            "AgentPlan is required."
        )

    intent_text = (
        plan.intent or ""
    ).lower().strip()

    analytical_text = (
        plan.analytical_question or ""
    ).lower().strip()

    combined = (
        f"{intent_text} {analytical_text}"
    )

    query_intent = QueryIntent(
        original_query=plan.query,
        tickers=list(plan.tickers),
        entities=list(plan.entities),
    )

    # ---------------------------------------------------------
    # Canonical financial intent
    # ---------------------------------------------------------

    if "price" in combined:
        query_intent.add_intent("price")

    if "fundamental" in combined:
        query_intent.add_intent(
            "fundamentals"
        )

    if "valuation" in combined:
        query_intent.add_intent(
            "valuation"
        )

    if "volume" in combined:
        query_intent.add_intent(
            "volume"
        )

    if (
        "news" in combined
        or "event" in combined
    ):
        query_intent.add_intent(
            "news"
        )

    # ---------------------------------------------------------
    # Canonical operations
    # ---------------------------------------------------------

    comparison_requested = (
        "compar" in combined
        or (
            len(plan.tickers) >= 2
            and plan.requires_calculation
        )
    )

    if comparison_requested:
        query_intent.add_operation(
            "compare"
        )

    # ---------------------------------------------------------
    # Canonical metrics
    # ---------------------------------------------------------

    if "price" in combined:
        query_intent.add_metric(
            "share_price"
        )

    if (
        "performance" in combined
        or "return" in combined
    ):
        query_intent.add_metric(
            "return"
        )

    # ---------------------------------------------------------
    # Temporal semantics
    #
    # Exact calendar boundaries will be added by the
    # deterministic temporal-grounding layer.
    # ---------------------------------------------------------

        # ---------------------------------------------------------
    # Temporal grounding
    # ---------------------------------------------------------

    if plan.latest:
        query_intent.date_range = {
            "type": "latest"
        }

    elif plan.temporal_expression:
        query_intent.date_range = (
            ground_temporal_expression(
                plan.temporal_expression
            )
        )

    return query_intent