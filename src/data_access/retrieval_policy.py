from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


PRICE_INTENTS = {
    "price",
}

FUNDAMENTAL_INTENTS = {
    "fundamentals",
}

VOLUME_INTENTS = {
    "volume",
}

NEWS_INTENTS = {
    "news",
}

DOCUMENT_INTENTS = {
    "research_report",
}

VALUATION_INTENTS = {
    "valuation",
}

SQL_INTENTS = {
    "analytics",
    "calculation",
}



@dataclass
class RetrievalPlan:
    """
    Structured retrieval plan.

    `tickers` is the canonical multi-entity field.

    `ticker` is retained for backward compatibility with the
    existing single-ticker retrieval executor and tests.

    `date_range` carries temporal semantics from QueryIntent.
    """

    tools: list[str] = field(default_factory=list)

    tickers: list[str] = field(default_factory=list)

    ticker: Optional[str] = None

    event_id: Optional[str] = None

    date_range: Optional[dict[str, str]] = None

    rationale: dict[str, str] = field(default_factory=dict)
    def __post_init__(self):
        # Normalize tickers.
        normalized = []

        for ticker in self.tickers:
            if ticker:
                ticker = ticker.upper()

                if ticker not in normalized:
                    normalized.append(ticker)

        # Preserve old `ticker=` constructor behavior.
        if self.ticker:
            ticker = self.ticker.upper()

            if ticker not in normalized:
                normalized.insert(0, ticker)

        self.tickers = normalized

        # Maintain backward compatibility.
        if self.ticker is None and len(self.tickers) == 1:
            self.ticker = self.tickers[0]

        if self.ticker is not None:
            self.ticker = self.ticker.upper()

    def add_tool(
        self,
        tool_name: str,
        rationale: Optional[str] = None,
    ) -> None:

        if tool_name not in self.tools:
            self.tools.append(tool_name)

        if rationale:
            self.rationale[tool_name] = rationale


def _normalize_tickers(
    ticker: Optional[str] = None,
    tickers: Optional[list[str]] = None,
) -> list[str]:

    result = []

    if tickers:
        for value in tickers:
            if value:
                value = value.upper()

                if value not in result:
                    result.append(value)

    if ticker:
        ticker = ticker.upper()

        if ticker not in result:
            result.insert(0, ticker)

    return result


def build_retrieval_plan(
    intents: list[str],
    ticker: Optional[str] = None,
    tickers: Optional[list[str]] = None,
    event_id: Optional[str] = None,
    date_range: Optional[dict[str, str]] = None,
) -> RetrievalPlan:

    if intents is None:
        intents = []

    normalized_intents = [
        intent.lower().strip()
        for intent in intents
        if intent and intent.strip()
    ]

    normalized_tickers = _normalize_tickers(
        ticker=ticker,
        tickers=tickers,
    )

    plan = RetrievalPlan(
        tickers=normalized_tickers,
        ticker=(
            normalized_tickers[0]
            if len(normalized_tickers) == 1
            else None
        ),
        event_id=event_id,
        date_range=date_range,
    )

    # ---------------------------------------------------------
    # Price
    # ---------------------------------------------------------

    if any(
        intent in PRICE_INTENTS
        for intent in normalized_intents
    ):
        plan.add_tool(
            "get_prices",
            "Retrieve historical market prices.",
        )

    # ---------------------------------------------------------
    # Fundamentals
    # ---------------------------------------------------------

    if any(
        intent in FUNDAMENTAL_INTENTS
        for intent in normalized_intents
    ):
        plan.add_tool(
            "get_fundamental_data",
            "Retrieve fundamental financial data.",
        )

    # ---------------------------------------------------------
    # Volume
    # ---------------------------------------------------------

    if any(
        intent in VOLUME_INTENTS
        for intent in normalized_intents
    ):
        plan.add_tool(
            "get_volume",
            "Retrieve historical trading volume.",
        )

    # ---------------------------------------------------------
    # News
    # ---------------------------------------------------------

    if any(
        intent in NEWS_INTENTS
        for intent in normalized_intents
    ):
        plan.add_tool(
            "search_news",
            "Search synthetic market/news sources.",
        )

    # ---------------------------------------------------------
    # Research documents
    # ---------------------------------------------------------

    if any(
        intent in DOCUMENT_INTENTS
        for intent in normalized_intents
    ):
        plan.add_tool(
            "search_documents",
            "Search layout-aware research documents.",
        )

    # ---------------------------------------------------------
    # Valuation / internal API
    # ---------------------------------------------------------

    if any(
        intent in VALUATION_INTENTS
        for intent in normalized_intents
    ):
        plan.add_tool(
            "get_internal_api",
            "Retrieve internal valuation/scenario data.",
        )

    # ---------------------------------------------------------
    # Explicit analytical intent
    # ---------------------------------------------------------

    if any(
        intent in SQL_INTENTS
        for intent in normalized_intents
    ):
        plan.add_tool(
            "run_sql",
            "Execute an explicitly supplied analytical SQL query.",
        )

    return plan
def build_retrieval_plan_from_intent(
    query_intent,
) -> RetrievalPlan:
    """
    Convert a QueryIntent object into a RetrievalPlan.

    QueryIntent is the semantic contract produced by the
    query-understanding layer.

    RetrievalPlan is the deterministic execution contract
    consumed by the retrieval executor.
    """

    if query_intent is None:
        raise ValueError(
            "query_intent cannot be None."
        )

    # ---------------------------------------------------------
    # Extract tickers.
    # ---------------------------------------------------------

    tickers = list(
        getattr(
            query_intent,
            "tickers",
            [],
        )
        or []
    )

    # ---------------------------------------------------------
    # Extract intents.
    # ---------------------------------------------------------

    intents = list(
        getattr(
            query_intent,
            "intents",
            [],
        )
        or []
    )

    # ---------------------------------------------------------
    # Extract event.
    #
    # Current QueryIntent supports event_ids as a list.
    # RetrievalPlan currently supports one event_id.
    #
    # We deliberately use the first event for now.
    # Multi-event retrieval can be introduced separately
    # rather than silently changing the current contract.
    # ---------------------------------------------------------

    event_ids = list(
        getattr(
            query_intent,
            "event_ids",
            [],
        )
        or []
    )

    date_range = getattr(
        query_intent,
        "date_range",
        None,
    )

    event_id = (
        event_ids[0]
        if event_ids
        else None
    )

    # ---------------------------------------------------------
    # Build the normal deterministic plan.
    # ---------------------------------------------------------

    plan = build_retrieval_plan(
        intents=intents,
        tickers=tickers,
        event_id=event_id,
        date_range=date_range,
    )

    # ---------------------------------------------------------
    # Add source-aware rationale.
    #
    # The tools are still determined by the intent.
    # requested_sources is metadata/context, not a second
    # competing routing system.
    # ---------------------------------------------------------

    requested_sources = list(
        getattr(
            query_intent,
            "requested_sources",
            [],
        )
        or []
    )

    if requested_sources:

        plan.rationale[
            "requested_sources"
        ] = (
            "Query requested source types: "
            + ", ".join(requested_sources)
        )

    # ---------------------------------------------------------
    # Preserve the original query for downstream layers.
    #
    # RetrievalPlan intentionally remains deterministic.
    # ---------------------------------------------------------

    original_query = getattr(
        query_intent,
        "original_query",
        "",
    )

    if original_query:

        plan.rationale[
            "original_query"
        ] = original_query
    
    if date_range:
        plan.rationale["date_range"] = str(date_range)
        
    return plan