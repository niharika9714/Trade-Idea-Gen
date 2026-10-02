from __future__ import annotations

import re
from typing import Optional

from src.data_access.query_intent import QueryIntent


SUPPORTED_TICKERS = {
    "D05": "DBS",
    "O39": "OCBC",
    "U11": "UOB",
    "HSBA": "HSBC",
    "STAN": "Standard Chartered",
}


INTENT_KEYWORDS = {
    "price": [
        "price",
        "share price",
        "stock price",
        "performance",
        "return",
        "returns",
    ],

    "fundamentals": [
        "fundamental",
        "fundamentals",
        "revenue",
        "profit",
        "earnings",
        "eps",
        "roe",
        "nim",
        "net interest margin",
    ],

    "volume": [
        "volume",
        "trading volume",
        "turnover",
    ],

    "news": [
        "news",
        "headline",
        "headlines",
        "market news",
        "announcement",
    ],

    "research_report": [
        "research report",
        "research",
        "analyst report",
        "investment report",
        "investment note",
        "earnings deck",
        "earnings presentation",
        "presentation",
        "investment committee",
    ],

    "valuation": [
        "valuation",
        "valued",
        "target price",
        "price target",
        "pe",
        "p/e",
        "pb",
        "p/b",
        "multiple",
    ],
}


METRIC_KEYWORDS = {
    "share_price": [
        "share price",
        "stock price",
        "share prices",
        "stock prices",
    ],

    "return": [
        "return",
        "returns",
        "performance",
    ],

    "revenue": [
        "revenue",
    ],

    "profit": [
        "profit",
        "net profit",
        "net income",
    ],

    "eps": [
        "eps",
        "earnings per share",
    ],

    "roe": [
        "roe",
        "return on equity",
    ],

    "nim": [
        "nim",
        "net interest margin",
    ],

    "volume": [
        "volume",
        "trading volume",
    ],

    "pe": [
        "pe",
        "p/e",
        "price earnings",
        "price-to-earnings",
    ],

    "pb": [
        "pb",
        "p/b",
        "price to book",
        "price-to-book",
    ],

    "target_price": [
        "target price",
        "price target",
    ],
}


OPERATION_KEYWORDS = {
    "compare": [
        "compare",
        "comparison",
        "versus",
        "vs",
        "against",
        "relative to",
    ],

    "calculate": [
        "calculate",
        "compute",
        "work out",
        "derive",
    ],

    "trend": [
        "trend",
        "trending",
        "over time",
        "historical trend",
    ],

    "change": [
        "change",
        "changed",
        "increase",
        "decrease",
        "growth",
    ],

    "rank": [
        "rank",
        "ranking",
        "highest",
        "lowest",
        "top",
        "bottom",
    ],
}


SOURCE_KEYWORDS = {
    "news": [
        "news",
        "headline",
        "announcement",
    ],

    "research_report": [
        "research report",
        "research",
        "analyst report",
        "investment note",
        "investment committee",
    ],

    "email": [
        "email",
        "emails",
        "mail",
        "outlook",
    ],

    "market_data": [
        "market data",
        "price",
        "volume",
    ],

    "internal_api": [
        "valuation api",
        "internal valuation",
        "scenario",
        "scenario analysis",
    ],
}


EVENT_PATTERN = re.compile(
    r"\b([A-Z0-9]+-EVENT-\d{3})\b",
    flags=re.IGNORECASE,
)


def _contains_keyword(text: str, keyword: str) -> bool:
    """
    Avoid accidental substring matching where possible.
    """

    text = text.lower()
    keyword = keyword.lower()

    if " " in keyword or "-" in keyword or "/" in keyword:
        return keyword in text

    return re.search(
        rf"\b{re.escape(keyword)}\b",
        text,
    ) is not None


def _detect_tickers(query: str) -> list[str]:
    query_upper = query.upper()

    found = []

    for ticker in SUPPORTED_TICKERS:
        if re.search(
            rf"\b{re.escape(ticker)}\b",
            query_upper,
        ):
            found.append(ticker)

    return found


def _detect_intents(query: str) -> list[str]:
    intents = []

    for intent, keywords in INTENT_KEYWORDS.items():

        if any(
            _contains_keyword(query, keyword)
            for keyword in keywords
        ):
            intents.append(intent)

    return intents


def _detect_metrics(query: str) -> list[str]:
    metrics = []

    for metric, keywords in METRIC_KEYWORDS.items():

        if any(
            _contains_keyword(query, keyword)
            for keyword in keywords
        ):
            metrics.append(metric)

    return metrics


def _detect_operations(query: str) -> list[str]:
    operations = []

    for operation, keywords in OPERATION_KEYWORDS.items():

        if any(
            _contains_keyword(query, keyword)
            for keyword in keywords
        ):
            operations.append(operation)

    return operations


def _detect_sources(query: str) -> list[str]:
    sources = []

    for source, keywords in SOURCE_KEYWORDS.items():

        if any(
            _contains_keyword(query, keyword)
            for keyword in keywords
        ):
            sources.append(source)

    return sources


def _detect_event_ids(query: str) -> list[str]:
    matches = EVENT_PATTERN.findall(query)

    return list(
        dict.fromkeys(
            match.upper()
            for match in matches
        )
    )


def _detect_date_range(
    query: str,
) -> Optional[dict[str, str]]:

    query_lower = query.lower()

    if "latest" in query_lower:
        return {
            "type": "latest",
        }

    if "historical" in query_lower:
        return {
            "type": "historical",
        }

    if "last year" in query_lower:
        return {
            "type": "relative",
            "period": "last_year",
        }

    if "last month" in query_lower:
        return {
            "type": "relative",
            "period": "last_month",
        }

    if "last quarter" in query_lower:
        return {
            "type": "relative",
            "period": "last_quarter",
        }

    if "this year" in query_lower:
        return {
            "type": "relative",
            "period": "this_year",
        }

    if "this quarter" in query_lower:
        return {
            "type": "relative",
            "period": "this_quarter",
        }

    return None


def understand_query(
    query: str,
) -> QueryIntent:

    if not isinstance(query, str):
        raise TypeError("Query must be a string.")

    query = query.strip()

    if not query:
        raise ValueError("Query cannot be empty.")

    result = QueryIntent(
        original_query=query,
    )

    # ---------------------------------------------------------
    # Entities
    # ---------------------------------------------------------

    tickers = _detect_tickers(query)

    for ticker in tickers:
        result.add_ticker(ticker)

    result.entities.extend(
        SUPPORTED_TICKERS[ticker]
        for ticker in tickers
    )

    # ---------------------------------------------------------
    # Intents
    # ---------------------------------------------------------

    for intent in _detect_intents(query):
        result.add_intent(intent)

    # ---------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------

    for metric in _detect_metrics(query):
        result.add_metric(metric)

    # ---------------------------------------------------------
    # Operations
    # ---------------------------------------------------------

    for operation in _detect_operations(query):
        result.add_operation(operation)

    # ---------------------------------------------------------
    # Sources
    # ---------------------------------------------------------

    for source in _detect_sources(query):
        result.add_source(source)

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------

    for event_id in _detect_event_ids(query):
        result.add_event(event_id)

    # ---------------------------------------------------------
    # Time
    # ---------------------------------------------------------

    result.date_range = _detect_date_range(query)

    return result