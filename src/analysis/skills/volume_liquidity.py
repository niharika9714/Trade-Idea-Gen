from src.analysis.skill_contract import (
    SkillContext,
    SkillResult,
    SkillSpec,
)
from src.analysis.evidence_analysis import AnalysisFact


def execute_volume_liquidity(
    context: SkillContext,
) -> SkillResult:

    facts = []
    evidence_ids = []
    citations = []

    for evidence in context.evidence_bundle:

        if evidence.source_type != "sql":
            continue

        content = evidence.content

        if not isinstance(content, dict):
            continue

        if "volume" not in content:
            continue

        ticker = (
            content.get("ticker")
            or evidence.ticker
        )

        fact = AnalysisFact(
            entity=ticker,
            metric="volume",
            value=content["volume"],
            unit="shares",
            date=(
                content.get("trade_date")
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

    if not facts:
        return SkillResult(
            skill_name="volume_liquidity",
            status="no_data",
            limitations=[
                "No trading-volume evidence was found."
            ],
        )

    return SkillResult(
        skill_name="volume_liquidity",
        status="success",
        facts=facts,
        evidence_ids=evidence_ids,
        citations=citations,
        metadata={
            "fact_count": len(facts),
        },
    )


VOLUME_LIQUIDITY_SKILL = SkillSpec(
    name="volume_liquidity",
    description=(
        "Analyses trading volume and "
        "liquidity-related market activity."
    ),
    required_intents=["volume"],
    required_tools=["get_volume"],
    trigger_keywords=[
        "volume",
        "trading volume",
        "liquidity",
        "turnover",
    ],
    execute_function=execute_volume_liquidity,
    priority=50,
)