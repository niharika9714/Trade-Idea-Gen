from __future__ import annotations

import re
from typing import Any, Optional

from src.data_access.retrieval_policy import RetrievalPlan
from src.tools.retrieval_tools import execute_retrieval_tool
from src.provenance.evidence import EvidenceBundle


def _empty_bundle() -> EvidenceBundle:
    return EvidenceBundle()


def _merge_bundle(
    target: EvidenceBundle,
    source: EvidenceBundle,
) -> None:
    target.merge(source)


def _build_entity_query(
    query: str,
    plan: RetrievalPlan,
    ticker: Optional[str],
) -> str:
    """
    Convert a multi-entity user query into a retrieval-local query.

    Entity names and generic conversational/retrieval-control words
    are removed because entity selection is already handled through
    the ticker parameter.

    Example:

        "Compare D05 and O39 latest news"

    becomes:

        ""

    for the news search.

    An empty query is intentional: search_news() will then return the
    most recent articles for the supplied ticker.
    """

    if not query:
        return ""

    entity_query = query

    # ---------------------------------------------------------
    # Remove all entities participating in the retrieval plan.
    # ---------------------------------------------------------

    for plan_ticker in plan.tickers:

        if not plan_ticker:
            continue

        entity_query = re.sub(
            rf"\b{re.escape(plan_ticker)}\b",
            " ",
            entity_query,
            flags=re.IGNORECASE,
        )

    # Backward-compatible single ticker.
    if plan.ticker:

        entity_query = re.sub(
            rf"\b{re.escape(plan.ticker)}\b",
            " ",
            entity_query,
            flags=re.IGNORECASE,
        )

    # ---------------------------------------------------------
    # Remove generic retrieval/control language.
    #
    # These words describe HOW the user wants retrieval performed,
    # rather than WHAT article content should be searched.
    # ---------------------------------------------------------

    retrieval_stopwords = {
        "compare",
        "comparison",
        "show",
        "find",
        "get",
        "give",
        "tell",
        "latest",
        "recent",
        "current",
        "historical",
        "history",
        "news",
        "article",
        "articles",
        "information",
        "info",
        "data",
        "about",
        "on",
        "for",
        "the",
        "and",
        "or",
        "of",
        "what",
        "is",
        "are",
        "was",
        "were",
        "me",
        "please",
    }

    tokens = re.findall(
        r"\b[A-Za-z0-9_-]+\b",
        entity_query,
    )

    meaningful_tokens = [
        token
        for token in tokens
        if token.lower() not in retrieval_stopwords
    ]

    entity_query = " ".join(
        meaningful_tokens
    ).strip()

    return entity_query


def _build_tool_arguments(
    tool_name: str,
    plan: RetrievalPlan,
    ticker: Optional[str],
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20,
    latest: bool = False,
) -> dict[str, Any]:

    event_id = plan.event_id

    if tool_name == "get_prices":

        if not ticker:
            raise ValueError(
                "Ticker is required for get_prices."
            )

        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "latest": latest,
        }

    if tool_name == "get_fundamental_data":

        if not ticker:
            raise ValueError(
                "Ticker is required for get_fundamental_data."
            )

        return {
            "ticker": ticker,
            "limit": limit,
        }

    if tool_name == "get_volume":

        if not ticker:
            raise ValueError(
                "Ticker is required for get_volume."
            )

        return {
            "ticker": ticker,
            "limit": limit,
        }

    if tool_name == "search_news":

        return {
            "query": query,
            "ticker": ticker,
            "event_id": event_id,
            "limit": limit,
        }

    if tool_name == "search_documents":

        return {
            "query": query,
            "ticker": ticker,
            "event_id": event_id,
            "max_results": limit,
        }

    if tool_name == "get_internal_api":

        if not ticker:
            raise ValueError(
                "Ticker is required for get_internal_api."
            )

        return {
            "ticker": ticker,
        }

    if tool_name == "run_sql":

        raise ValueError(
            "run_sql requires an explicit analytical query. "
            "The generic retrieval planner will not invent SQL."
        )

    if tool_name == "discover_sources":

        return {
            "query": query,
            "ticker": ticker,
            "event_id": event_id,
            "max_results": limit,
        }

    if tool_name == "get_document":

        raise ValueError(
            "get_document requires an explicit source_path."
        )

    raise ValueError(
        f"Unsupported retrieval tool: {tool_name}"
    )


def _execute_for_ticker(
    plan: RetrievalPlan,
    ticker: Optional[str],
    query: str,
    start_date: Optional[str],
    end_date: Optional[str],
    limit: int,
    latest: bool = False,
) -> EvidenceBundle:

    bundle = _empty_bundle()

    # Make the search text local to this entity.
    entity_query = _build_entity_query(
        query=query,
        plan=plan,
        ticker=ticker,
    )

    for tool_name in plan.tools:

        arguments = _build_tool_arguments(
            tool_name=tool_name,
            plan=plan,
            ticker=ticker,
            query=entity_query,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            latest=latest,
        )

        result = execute_retrieval_tool(
            tool_name,
            arguments,
        )

        if isinstance(result, EvidenceBundle):

            _merge_bundle(
                bundle,
                result,
            )

            continue

        if tool_name == "discover_sources":
            continue

        raise TypeError(
            f"Tool '{tool_name}' returned unsupported "
            f"result type: {type(result).__name__}"
        )

    return bundle


def execute_retrieval_plan(
    plan: RetrievalPlan,
    query: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20,
) -> EvidenceBundle:

    if not isinstance(plan, RetrievalPlan):
        raise TypeError(
            "plan must be a RetrievalPlan."
        )

    # ---------------------------------------------------------
    # Backward compatibility:
    #
    # Older callers/tests may provide only the RetrievalPlan.
    # build_retrieval_plan_from_intent() preserves the original
    # user query in plan.rationale["original_query"].
    # ---------------------------------------------------------

    if query is None:

        query = plan.rationale.get(
            "original_query",
            "",
        )

    if not isinstance(query, str):
        raise TypeError(
            "query must be a string."
        )

    if not query.strip():
        raise ValueError(
            "query cannot be empty."
        )

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise TypeError(
            "limit must be an integer."
        )

    if limit <= 0:
        raise ValueError(
            "limit must be greater than zero."
        )
    # ---------------------------------------------------------
    # Resolve temporal boundaries from the RetrievalPlan.
    #
    # Explicit function arguments take precedence for backward
    # compatibility. Otherwise, use the deterministic date range
    # already grounded into the RetrievalPlan.
    # ---------------------------------------------------------

    if plan.date_range:
        latest = False

        date_range_type = plan.date_range.get(
            "type"
        )

        if date_range_type == "absolute":

            if start_date is None:
                start_date = plan.date_range.get(
                    "start_date"
                )

            if end_date is None:
                end_date = plan.date_range.get(
                    "end_date"
                )

        elif date_range_type == "latest":
            # Latest semantics are handled separately by tools
            # that support latest retrieval.
            latest = True

    # ---------------------------------------------------------
    # Bounded historical ranges must retrieve the complete
    # requested period.
    #
    # The default retrieval limit is appropriate for unbounded
    # discovery, but must not silently truncate an explicitly
    # requested analytical period.
    # ---------------------------------------------------------

    execution_limit = limit
    if latest:
        execution_limit = 1

    if (
        plan.date_range
        and plan.date_range.get("type") == "absolute"
        and start_date
        and end_date
    ):
        execution_limit = 500
    # ---------------------------------------------------------
    # Determine execution entities.
    # ---------------------------------------------------------

    tickers = list(plan.tickers)

    # Backward compatibility with old RetrievalPlan(ticker="D05")
    if not tickers and plan.ticker:
        tickers = [plan.ticker.upper()]

    # ---------------------------------------------------------
    # No ticker is acceptable for tools that can operate
    # without ticker context.
    # ---------------------------------------------------------

    if not tickers:

        return _execute_for_ticker(
            plan=plan,
            ticker=None,
            query=query,
            start_date=start_date,
            end_date=end_date,
            limit=execution_limit,
            latest=latest,
        )

    # ---------------------------------------------------------
    # Fan out across every entity.
    # ---------------------------------------------------------

    final_bundle = _empty_bundle()

    for ticker in tickers:

        ticker_bundle = _execute_for_ticker(
            plan=plan,
            ticker=ticker,
            query=query,
            start_date=start_date,
            end_date=end_date,
            limit=execution_limit,
            latest=latest,
        )

        _merge_bundle(
            final_bundle,
            ticker_bundle,
        )

    return final_bundle