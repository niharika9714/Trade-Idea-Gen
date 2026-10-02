from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.provenance.evidence import EvidenceBundle


@dataclass
class AnalysisFact:
    """
    A normalized fact derived directly from Evidence.

    The fact retains the evidence IDs and citations that support it.
    """

    entity: Optional[str]
    metric: str
    value: Any
    unit: Optional[str] = None
    date: Optional[str] = None

    evidence_ids: list[str] = field(
        default_factory=list
    )

    citations: list[str] = field(
        default_factory=list
    )

    source_types: list[str] = field(
        default_factory=list
    )


@dataclass
class DerivedMetric:
    """
    A calculated value whose inputs remain explicitly traceable.
    """

    entity: Optional[str]
    metric: str
    value: Any
    unit: Optional[str] = None

    input_evidence_ids: list[str] = field(
        default_factory=list
    )

    input_citations: list[str] = field(
        default_factory=list
    )

    calculation: str = ""


@dataclass
class AnalysisResult:
    """
    Output of the deterministic evidence-analysis layer.
    """

    facts: list[AnalysisFact] = field(
        default_factory=list
    )

    derived_metrics: list[DerivedMetric] = field(
        default_factory=list
    )

    entities: list[str] = field(
        default_factory=list
    )

    citations: list[str] = field(
        default_factory=list
    )

    def add_fact(
        self,
        fact: AnalysisFact,
    ) -> None:

        self.facts.append(fact)

        if fact.entity:
            if fact.entity not in self.entities:
                self.entities.append(
                    fact.entity
                )

        for citation in fact.citations:
            if citation not in self.citations:
                self.citations.append(
                    citation
                )

    def add_derived_metric(
        self,
        metric: DerivedMetric,
    ) -> None:

        self.derived_metrics.append(
            metric
        )

        if metric.entity:
            if metric.entity not in self.entities:
                self.entities.append(
                    metric.entity
                )

        for citation in metric.input_citations:
            if citation not in self.citations:
                self.citations.append(
                    citation
                )

    def to_dict(self) -> dict[str, Any]:

        return {
            "facts": [
                {
                    "entity": fact.entity,
                    "metric": fact.metric,
                    "value": fact.value,
                    "unit": fact.unit,
                    "date": fact.date,
                    "evidence_ids": fact.evidence_ids,
                    "citations": fact.citations,
                    "source_types": fact.source_types,
                }
                for fact in self.facts
            ],
            "derived_metrics": [
                {
                    "entity": metric.entity,
                    "metric": metric.metric,
                    "value": metric.value,
                    "unit": metric.unit,
                    "input_evidence_ids": (
                        metric.input_evidence_ids
                    ),
                    "input_citations": (
                        metric.input_citations
                    ),
                    "calculation": metric.calculation,
                }
                for metric in self.derived_metrics
            ],
            "entities": self.entities,
            "citations": self.citations,
        }


def _unique(values: list[str]) -> list[str]:

    result = []

    for value in values:

        if value and value not in result:
            result.append(value)

    return result


def _content_to_dict(
    evidence,
) -> dict[str, Any]:

    content = evidence.content

    if isinstance(content, dict):
        return content

    return {
        "content": content
    }


def extract_sql_facts(
    bundle: EvidenceBundle,
) -> AnalysisResult:
    """
    Extract basic facts from SQL Evidence.

    This function does not calculate or infer investment conclusions.
    It simply exposes the underlying structured values.
    """

    result = AnalysisResult()

    for evidence in bundle:

        if evidence.source_type != "sql":
            continue

        row = _content_to_dict(
            evidence
        )

        ticker = (
            evidence.ticker
            or row.get("ticker")
        )

        date = (
            row.get("trade_date")
            or row.get("report_date")
            or row.get("date")
        )

        # ---------------------------------------------------------
        # Daily price
        # ---------------------------------------------------------

        if "close_price" in row:

            fact = AnalysisFact(
                entity=ticker,
                metric="close_price",
                value=row.get(
                    "close_price"
                ),
                unit="price",
                date=date,
                evidence_ids=[
                    evidence.evidence_id
                ],
                citations=[
                    evidence.citation
                ],
                source_types=[
                    evidence.source_type
                ],
            )

            result.add_fact(
                fact
            )

        # ---------------------------------------------------------
        # Volume
        # ---------------------------------------------------------

        if "volume" in row:

            fact = AnalysisFact(
                entity=ticker,
                metric="volume",
                value=row.get(
                    "volume"
                ),
                unit="shares",
                date=date,
                evidence_ids=[
                    evidence.evidence_id
                ],
                citations=[
                    evidence.citation
                ],
                source_types=[
                    evidence.source_type
                ],
            )

            result.add_fact(
                fact
            )

        # ---------------------------------------------------------
        # Fundamentals
        # ---------------------------------------------------------

        fundamental_metrics = [
            "revenue",
            "net_income",
            "eps",
            "roe",
            "nim",
            "pe",
            "pb",
            "target_price",
        ]

        for metric in fundamental_metrics:

            if metric not in row:
                continue

            fact = AnalysisFact(
                entity=ticker,
                metric=metric,
                value=row.get(metric),
                date=date,
                evidence_ids=[
                    evidence.evidence_id
                ],
                citations=[
                    evidence.citation
                ],
                source_types=[
                    evidence.source_type
                ],
            )

            result.add_fact(
                fact
            )

    return result


def calculate_return(
    bundle: EvidenceBundle,
    ticker: str,
    start_date: str,
    end_date: str,
) -> DerivedMetric:
    """
    Calculate price return from two directly retrieved
    daily-price Evidence records.

    Formula:

        return = (end_price - start_price) / start_price

    No external values are accepted.
    """

    ticker = ticker.upper()

    start_evidence = None
    end_evidence = None

    for evidence in bundle:

        if evidence.source_type != "sql":
            continue

        if evidence.ticker != ticker:
            continue

        row = _content_to_dict(
            evidence
        )

        trade_date = row.get(
            "trade_date"
        )

        if trade_date == start_date:
            if "close_price" in row:
                start_evidence = evidence

        if trade_date == end_date:
            if "close_price" in row:
                end_evidence = evidence

    if start_evidence is None:
        raise ValueError(
            f"No price evidence found for "
            f"{ticker} on {start_date}."
        )

    if end_evidence is None:
        raise ValueError(
            f"No price evidence found for "
            f"{ticker} on {end_date}."
        )

    start_row = _content_to_dict(
        start_evidence
    )

    end_row = _content_to_dict(
        end_evidence
    )

    start_price = float(
        start_row["close_price"]
    )

    end_price = float(
        end_row["close_price"]
    )

    if start_price == 0:
        raise ValueError(
            "Cannot calculate return from zero "
            "starting price."
        )

    value = (
        end_price - start_price
    ) / start_price

    return DerivedMetric(
        entity=ticker,
        metric="return",
        value=value,
        unit="decimal",
        input_evidence_ids=[
            start_evidence.evidence_id,
            end_evidence.evidence_id,
        ],
        input_citations=[
            start_evidence.citation,
            end_evidence.citation,
        ],
        calculation=(
            f"({end_price} - {start_price}) "
            f"/ {start_price}"
        ),
    )


def group_facts_by_entity(
    analysis: AnalysisResult,
) -> dict[str, list[AnalysisFact]]:

    grouped: dict[
        str,
        list[AnalysisFact]
    ] = {}

    for fact in analysis.facts:

        if not fact.entity:
            continue

        grouped.setdefault(
            fact.entity,
            [],
        ).append(
            fact
        )

    return grouped