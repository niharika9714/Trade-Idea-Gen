from src.analysis.skill_contract import (
    SkillContext,
    SkillResult,
    SkillSpec,
)


def execute_event_analysis(
    context: SkillContext,
) -> SkillResult:

    facts = []
    evidence_ids = []
    citations = []

    for evidence in context.evidence_bundle:

        if evidence.source_type not in {
            "news",
            "pdf",
            "pptx",
            "docx",
            "msg",
        }:
            continue

        evidence_ids.append(
            evidence.evidence_id
        )

        citations.append(
            evidence.citation
        )

        facts.append(
            {
                "source_type": evidence.source_type,
                "content": evidence.content,
                "event_id": evidence.event_id,
                "ticker": evidence.ticker,
                "evidence_id": evidence.evidence_id,
                "citation": evidence.citation,
            }
        )

    if not facts:
        return SkillResult(
            skill_name="event_analysis",
            status="no_data",
            limitations=[
                "No event-related evidence was found."
            ],
        )

    return SkillResult(
        skill_name="event_analysis",
        status="success",
        facts=facts,
        evidence_ids=evidence_ids,
        citations=citations,
        metadata={
            "event_ids": list(
                dict.fromkeys(
                    fact["event_id"]
                    for fact in facts
                    if fact["event_id"]
                )
            ),
            "source_types": list(
                dict.fromkeys(
                    fact["source_type"]
                    for fact in facts
                )
            ),
        },
    )


EVENT_ANALYSIS_SKILL = SkillSpec(
    name="event_analysis",
    description=(
        "Analyses historical events using "
        "news and research-document evidence."
    ),
    required_intents=[
        "news",
        "research_report",
    ],
    required_tools=[
        "search_news",
        "search_documents",
    ],
    trigger_keywords=[
        "event",
        "why",
        "reaction",
        "earnings reaction",
        "historical event",
        "announcement",
        "news",
    ],
    execute_function=execute_event_analysis,
    priority=40,
)