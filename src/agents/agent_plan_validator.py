from __future__ import annotations

from src.agents.agent_plan_schema import AgentPlan


RETRIEVAL_REQUIRED_PHRASES = {
    "what do you know",
    "tell me about",
    "find information",
    "find out about",
    "information about",
    "explain",
    "describe",
    "what happened",
    "why",
    "who",
    "where",
    "when",
}


def _requires_retrieval(plan: AgentPlan) -> bool:
    """Determine whether the query obviously requires retrieval.

    This is NOT query understanding.

    It is a safety check preventing the LLM from producing an
    empty execution plan for an information-seeking question.
    """

    query = plan.query.lower().strip()

    if plan.tools:
        return False

    if plan.search_queries:
        return False

    if plan.requires_calculation:
        return True

    if plan.tickers:
        return True

    for phrase in RETRIEVAL_REQUIRED_PHRASES:
        if phrase in query:
            return True

    if plan.entities:
        return True

    return False


def _repair_financial_plan(
    plan: AgentPlan,
    available_tool_names: set[str],
) -> None:
    """
    Repair obvious financial planning omissions.

    This is a deterministic safety layer, not query understanding.
    Qwen remains the primary planner.
    """

    text = plan.query.lower()

    financial_price_terms = {
        "share price",
        "stock price",
        "closing price",
        "market price",
        "price history",
        "price performance",
    }

    volume_terms = {
        "volume",
        "trading volume",
        "traded volume",
    }

    fundamental_terms = {
        "revenue",
        "profit",
        "net income",
        "earnings",
        "eps",
        "roe",
        "nim",
        "fundamentals",
    }

    valuation_terms = {
        "valuation",
        "p/e",
        "pe",
        "p/b",
        "pb",
        "price-to-book",
        "target price",
    }

    news_terms = {
        "news",
        "announcement",
        "earnings announcement",
        "what happened",
        "market event",
        "reaction",
    }

    if not plan.tickers:
        return

    if plan.tools:
        return

    if (
        any(term in text for term in financial_price_terms)
        and "get_prices" in available_tool_names
    ):
        plan.tools = ["get_prices"]

    elif (
        any(term in text for term in volume_terms)
        and "get_volume" in available_tool_names
    ):
        plan.tools = ["get_volume"]

    elif (
        any(term in text for term in fundamental_terms)
        and "get_fundamental_data" in available_tool_names
    ):
        plan.tools = ["get_fundamental_data"]

    elif (
        any(term in text for term in valuation_terms)
        and "get_internal_api" in available_tool_names
    ):
        plan.tools = ["get_internal_api"]

    elif (
        any(term in text for term in news_terms)
        and "search_news" in available_tool_names
    ):
        plan.tools = ["search_news"]

    if any(
        term in text
        for term in {
            "latest",
            "current",
            "today",
            "today's",
            "as of today",
            "most recent",
        }
    ):
        plan.latest = True


def validate_agent_plan(
    plan: AgentPlan,
    available_tool_names: set[str],
) -> AgentPlan:

    if not isinstance(plan, AgentPlan):
        raise TypeError(
            "plan must be an AgentPlan"
        )

    if not plan.query.strip():
        raise ValueError(
            "Agent plan query is required."
        )

    if not plan.intent.strip():
        raise ValueError(
            "Agent plan intent is required."
        )

    unknown_tools = sorted(
        set(plan.tools)
        - set(available_tool_names)
    )

    if unknown_tools:
        raise ValueError(
            "Agent plan contains unregistered tools: "
            + ", ".join(unknown_tools)
        )

    plan.tools = list(
        dict.fromkeys(plan.tools)
    )

    plan.skills = list(
        dict.fromkeys(plan.skills)
    )

    plan.entities = list(
        dict.fromkeys(plan.entities)
    )

    plan.tickers = list(
        dict.fromkeys(plan.tickers)
    )

    plan.search_queries = [
        query.strip()
        for query in dict.fromkeys(
            plan.search_queries
        )
        if query and query.strip()
    ]
    _repair_financial_plan(
        plan=plan,
        available_tool_names=available_tool_names,
    )

    if (
        _requires_retrieval(plan)
        and not plan.tools
    ):
        if (
            plan.entities
            and "search_documents"
            in available_tool_names
        ):
            plan.tools = [
                "search_documents"
            ]

            if not plan.search_queries:
                plan.search_queries = list(
                    plan.entities
                )

    if not plan.requires_calculation:
        plan.analytical_question = None

    return plan