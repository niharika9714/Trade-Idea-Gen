from src.analysis.skill_contract import (
    SkillContext,
    SkillResult,
    SkillSpec,
)
from src.analysis.evidence_analysis import AnalysisFact


EARNINGS_METRICS = {
    "revenue",
    "net_income",
    "eps",
    "roe",
    "nim",
}


def execute_earnings_analysis(
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

        ticker = (
            content.get("ticker")
            or evidence.ticker
        )

        date = (
            content.get("report_date")
            or content.get("date")
        )

        for metric in EARNINGS_METRICS:

            if metric not in content:
                continue

            if content[metric] is None:
                continue

            fact = AnalysisFact(
                entity=ticker,
                metric=metric,
                value=content[metric],
                unit=(
                    "percentage"
                    if metric in {"roe", "nim"}
                    else "value"
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
            skill_name="earnings_analysis",
            status="no_data",
            limitations=[
                "No earnings/fundamental evidence "
                "was available."
            ],
        )

    return SkillResult(
        skill_name="earnings_analysis",
        status="success",
        facts=facts,
        evidence_ids=evidence_ids,
        citations=citations,
        metadata={
            "fact_count": len(facts),
            "metrics": sorted(
                set(
                    fact.metric
                    for fact in facts
                )
            ),
        },
    )


EARNINGS_ANALYSIS_SKILL = SkillSpec(
    name="earnings_analysis",
    description=(
        "Analyses earnings and fundamental "
        "financial metrics."
    ),
    required_intents=["fundamentals"],
    required_tools=[
        "get_fundamental_data"
    ],
    trigger_keywords=[
        "earnings",
        "revenue",
        "profit",
        "net income",
        "EPS",
        "ROE",
        "NIM",
        "fundamentals",
    ],
    execute_function=execute_earnings_analysis,
    priority=20,
)