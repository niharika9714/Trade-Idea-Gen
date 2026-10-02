from src.analysis.skill_contract import (
    SkillContext,
    SkillResult,
    SkillSpec,
)
from src.analysis.evidence_analysis import AnalysisFact


VALUATION_METRICS = {
    "pe",
    "pb",
    "target_price",
}


def execute_valuation_analysis(
    context: SkillContext,
) -> SkillResult:

    facts = []
    evidence_ids = []
    citations = []

    for evidence in context.evidence_bundle:

        if evidence.source_type not in {
            "internal_api",
            "sql",
        }:
            continue

        content = evidence.content

        if not isinstance(content, dict):
            continue

        ticker = (
            content.get("ticker")
            or evidence.ticker
        )

        date = (
            content.get("date")
            or content.get("report_date")
            or content.get("trade_date")
        )

        for metric in VALUATION_METRICS:

            if metric not in content:
                continue

            if content[metric] is None:
                continue

            fact = AnalysisFact(
                entity=ticker,
                metric=metric,
                value=content[metric],
                unit=(
                    "price"
                    if metric == "target_price"
                    else "multiple"
                ),
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

            facts.append(fact)

            evidence_ids.append(
                evidence.evidence_id
            )

            citations.append(
                evidence.citation
            )

    if not facts:
        return SkillResult(
            skill_name="valuation_analysis",
            status="no_data",
            limitations=[
                "No valuation evidence was available."
            ],
        )

    return SkillResult(
        skill_name="valuation_analysis",
        status="success",
        facts=facts,
        evidence_ids=evidence_ids,
        citations=citations,
        metadata={
            "fact_count": len(facts),
        },
    )


VALUATION_ANALYSIS_SKILL = SkillSpec(
    name="valuation_analysis",
    description=(
        "Analyses valuation multiples and "
        "target-price information."
    ),
    required_intents=["valuation"],
    required_tools=["get_internal_api"],
    trigger_keywords=[
        "valuation",
        "P/E",
        "PE",
        "P/B",
        "PB",
        "target price",
    ],
    execute_function=execute_valuation_analysis,
    priority=30,
)