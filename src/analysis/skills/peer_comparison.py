from src.analysis.skill_contract import (
    SkillContext,
    SkillResult,
    SkillSpec,
)
from src.analysis.evidence_analysis import AnalysisFact


def execute_peer_comparison(
    context: SkillContext,
) -> SkillResult:

    entities = list(
        dict.fromkeys(
            getattr(
                context.query_intent,
                "tickers",
                [],
            )
        )
    )

    if len(entities) < 2:
        return SkillResult(
            skill_name="peer_comparison",
            status="failed",
            limitations=[
                "Peer comparison requires at "
                "least two entities."
            ],
        )

    facts = []
    evidence_ids = []
    citations = []

    allowed_metrics = {
        "close_price",
        "revenue",
        "net_income",
        "eps",
        "roe",
        "nim",
        "pe",
        "pb",
        "target_price",
    }

    for evidence in context.evidence_bundle:

        if evidence.source_type not in {
            "sql",
            "internal_api",
        }:
            continue

        content = evidence.content

        if not isinstance(content, dict):
            continue

        ticker = (
            content.get("ticker")
            or evidence.ticker
        )

        if ticker not in entities:
            continue

        for metric in allowed_metrics:

            if metric not in content:
                continue

            if content[metric] is None:
                continue

            fact = AnalysisFact(
                entity=ticker,
                metric=metric,
                value=content[metric],
                unit="value",
                date=(
                    content.get("trade_date")
                    or content.get("report_date")
                    or content.get("date")
                ),
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

            facts.append(fact)
            evidence_ids.append(
                evidence.evidence_id
            )
            citations.append(
                evidence.citation
            )

    entities_with_data = sorted(
        set(
            fact.entity
            for fact in facts
            if fact.entity
        )
    )

    if len(entities_with_data) < 2:
        return SkillResult(
            skill_name="peer_comparison",
            status="no_data",
            facts=facts,
            evidence_ids=evidence_ids,
            citations=citations,
            limitations=[
                "Evidence was not available for "
                "at least two requested entities."
            ],
        )

    return SkillResult(
        skill_name="peer_comparison",
        status="success",
        facts=facts,
        evidence_ids=evidence_ids,
        citations=citations,
        metadata={
            "requested_entities": entities,
            "entities_with_data": entities_with_data,
            "fact_count": len(facts),
        },
    )


PEER_COMPARISON_SKILL = SkillSpec(
    name="peer_comparison",
    description=(
        "Compares investment metrics across "
        "multiple companies or instruments."
    ),
    required_intents=[
        "price",
        "fundamentals",
    ],
    required_tools=[
        "get_prices",
        "get_fundamental_data",
    ],
    trigger_keywords=[
        "compare",
        "comparison",
        "peer",
        "versus",
        "vs",
        "relative",
    ],
    execute_function=execute_peer_comparison,
    priority=5,
)