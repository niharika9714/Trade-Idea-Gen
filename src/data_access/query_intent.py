from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QueryIntent:
    """
    Structured representation of a user's investment research query.

    This is the contract between query understanding and retrieval.
    It does not execute retrieval or perform investment reasoning.
    """

    original_query: str

    tickers: list[str] = field(default_factory=list)

    intents: list[str] = field(default_factory=list)

    metrics: list[str] = field(default_factory=list)

    operations: list[str] = field(default_factory=list)

    date_range: Optional[dict[str, str]] = None

    event_ids: list[str] = field(default_factory=list)

    entities: list[str] = field(default_factory=list)

    requested_sources: list[str] = field(default_factory=list)

    confidence: float = 1.0

    def add_ticker(self, ticker: str) -> None:
        ticker = ticker.upper()

        if ticker not in self.tickers:
            self.tickers.append(ticker)

    def add_intent(self, intent: str) -> None:
        if intent not in self.intents:
            self.intents.append(intent)

    def add_metric(self, metric: str) -> None:
        if metric not in self.metrics:
            self.metrics.append(metric)

    def add_operation(self, operation: str) -> None:
        if operation not in self.operations:
            self.operations.append(operation)

    def add_event(self, event_id: str) -> None:
        if event_id not in self.event_ids:
            self.event_ids.append(event_id)

    def add_source(self, source: str) -> None:
        if source not in self.requested_sources:
            self.requested_sources.append(source)

    def to_dict(self) -> dict:
        return {
            "original_query": self.original_query,
            "tickers": self.tickers,
            "intents": self.intents,
            "metrics": self.metrics,
            "operations": self.operations,
            "date_range": self.date_range,
            "event_ids": self.event_ids,
            "entities": self.entities,
            "requested_sources": self.requested_sources,
            "confidence": self.confidence,
        }