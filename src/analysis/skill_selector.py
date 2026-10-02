from dataclasses import dataclass, field

from src.analysis.skill_contract import SkillSpec
from src.analysis.skill_registry import get_skill_registry


@dataclass
class SkillSelection:
    skills: list[str] = field(default_factory=list)
    rationale: dict[str, str] = field(
        default_factory=dict
    )

    def __post_init__(self):
        self.skills = list(
            dict.fromkeys(self.skills)
        )

    def to_dict(self):
        return {
            "skills": self.skills,
            "rationale": self.rationale,
        }


def _query_text(query_intent) -> str:

    return (
        getattr(
            query_intent,
            "original_query",
            "",
        )
        or ""
    ).lower()


def select_skills(
    query_intent,
) -> SkillSelection:

    registry = get_skill_registry()

    intents = set(
        getattr(
            query_intent,
            "intents",
            [],
        )
    )

    operations = set(
        getattr(
            query_intent,
            "operations",
            [],
        )
    )

    metrics = set(
        getattr(
            query_intent,
            "metrics",
            [],
        )
    )

    query_text = _query_text(
        query_intent
    )

    selected: list[SkillSpec] = []
    rationale = {}

    for skill in registry.list_skills():

        matched = False
        reason = None

        if skill.name == "peer_comparison":
            if (
                "compare" in operations
                and len(
                    getattr(
                        query_intent,
                        "tickers",
                        [],
                    )
                ) >= 2
            ):
                matched = True
                reason = (
                    "Multiple entities are being "
                    "compared."
                )

        elif skill.name == "price_performance":
            if (
                "price" in intents
                or "share_price" in metrics
                or "return" in metrics
            ):
                matched = True
                reason = (
                    "The query requires price "
                    "or performance analysis."
                )

        elif skill.name == "earnings_analysis":
            if (
                "fundamentals" in intents
                or any(
                    metric in metrics
                    for metric in {
                        "revenue",
                        "profit",
                        "eps",
                        "roe",
                        "nim",
                    }
                )
            ):
                matched = True
                reason = (
                    "The query requires fundamental "
                    "or earnings analysis."
                )

        elif skill.name == "valuation_analysis":
            if (
                "valuation" in intents
                or any(
                    metric in metrics
                    for metric in {
                        "pe",
                        "pb",
                        "target_price",
                    }
                )
            ):
                matched = True
                reason = (
                    "The query requires valuation "
                    "analysis."
                )

        elif skill.name == "event_analysis":
            if (
                "news" in intents
                and (
                    "event" in query_text
                    or getattr(
                        query_intent,
                        "event_ids",
                        [],
                    )
                    or "why" in query_text
                    or "reaction" in query_text
                )
            ):
                matched = True
                reason = (
                    "The query requires historical "
                    "event or news analysis."
                )

        elif skill.name == "volume_liquidity":
            if "volume" in intents:
                matched = True
                reason = (
                    "The query requires trading "
                    "volume analysis."
                )

        if matched:
            selected.append(skill)
            rationale[skill.name] = reason

    return SkillSelection(
        skills=[
            skill.name
            for skill in selected
        ],
        rationale=rationale,
    )