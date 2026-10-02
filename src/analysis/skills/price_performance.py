from src.analysis.skill_contract import (
    SkillContext,
    SkillResult,
    SkillSpec,
)
from src.analysis.evidence_analysis import (
    AnalysisFact,
    DerivedMetric,
)


def execute_price_performance(
    context: SkillContext,
) -> SkillResult:

    bundle = context.evidence_bundle

    facts = []
    derived_metrics = []
    evidence_ids = []
    citations = []

    for evidence in bundle:

        if evidence.source_type != "sql":
            continue

        content = evidence.content

        if not isinstance(content, dict):
            continue

        if "close_price" not in content:
            continue

        ticker = (
            content.get("ticker")
            or evidence.ticker
        )

        date = (
            content.get("trade_date")
            or content.get("date")
        )

        if ticker is None:
            continue

        fact = AnalysisFact(
            entity=ticker,
            metric="close_price",
            value=content["close_price"],
            unit="price",
            date=date,
            evidence_ids=[evidence.evidence_id],
            citations=[evidence.citation],
            source_types=[evidence.source_type],
        )

        facts.append(fact)

        evidence_ids.append(
            evidence.evidence_id
        )

        citations.append(
            evidence.citation
        )

    if not facts:
        return SkillResult(
            skill_name="price_performance",
            status="no_data",
            limitations=[
                "No close-price evidence was available."
            ],
        )

    by_entity = {}

    for fact in facts:
        by_entity.setdefault(
            fact.entity,
            [],
        ).append(fact)

    for ticker, ticker_facts in by_entity.items():

        dated = [
            fact
            for fact in ticker_facts
            if fact.date is not None
        ]

        dated.sort(
            key=lambda fact: fact.date
        )

        if len(dated) < 2:
            continue

        first = dated[0]
        last = dated[-1]

        if first.value in (None, 0):
            continue

        return_value = (
            float(last.value)
            - float(first.value)
        ) / float(first.value)

        derived_metrics.append(
            DerivedMetric(
                entity=ticker,
                metric="period_return",
                value=return_value,
                unit="decimal",
                input_evidence_ids=[
                    first.evidence_ids[0],
                    last.evidence_ids[0],
                ],
                input_citations=[
                    first.citations[0],
                    last.citations[0],
                ],
                calculation=(
                    f"({last.value} - {first.value}) "
                    f"/ {first.value}"
                ),
            )
        )

    return SkillResult(
        skill_name="price_performance",
        status="success",
        facts=facts,
        derived_metrics=derived_metrics,
        evidence_ids=evidence_ids,
        citations=citations,
        metadata={
            "fact_count": len(facts),
            "derived_metric_count": len(
                derived_metrics
            ),
        },
    )


PRICE_PERFORMANCE_SKILL = SkillSpec(
    name="price_performance",
    description=(
        "Analyses historical share prices and "
        "price performance."
    ),
    required_intents=["price"],
    required_tools=["get_prices"],
    trigger_keywords=[
        "price",
        "share price",
        "performance",
        "return",
        "stock performance",
    ],
    execute_function=execute_price_performance,
    priority=10,
)