from dataclasses import dataclass
from typing import Any

from src.analysis.skill_contract import SkillSpec


class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, SkillSpec] = {}

    def register(self, skill: SkillSpec):
        if skill.name in self._skills:
            raise ValueError(
                f"Skill already registered: {skill.name}"
            )

        self._skills[skill.name] = skill

    def get(self, name: str) -> SkillSpec:
        if name not in self._skills:
            raise KeyError(
                f"Unknown skill: {name}"
            )

        return self._skills[name]

    def list_skills(self) -> list[SkillSpec]:
        return sorted(
            self._skills.values(),
            key=lambda skill: (
                skill.priority,
                skill.name,
            ),
        )

    def names(self) -> list[str]:
        return [
            skill.name
            for skill in self.list_skills()
        ]

    def definitions(self) -> list[dict[str, Any]]:
        return [
            skill.to_dict()
            for skill in self.list_skills()
        ]


_default_registry = None


def get_skill_registry() -> SkillRegistry:
    global _default_registry

    if _default_registry is None:
        _default_registry = SkillRegistry()

        from src.analysis.skills.price_performance import (
            PRICE_PERFORMANCE_SKILL,
        )
        from src.analysis.skills.earnings_analysis import (
            EARNINGS_ANALYSIS_SKILL,
        )
        from src.analysis.skills.valuation_analysis import (
            VALUATION_ANALYSIS_SKILL,
        )
        from src.analysis.skills.peer_comparison import (
            PEER_COMPARISON_SKILL,
        )
        from src.analysis.skills.event_analysis import (
            EVENT_ANALYSIS_SKILL,
        )
        from src.analysis.skills.volume_liquidity import (
            VOLUME_LIQUIDITY_SKILL,
        )

        for skill in [
            PRICE_PERFORMANCE_SKILL,
            EARNINGS_ANALYSIS_SKILL,
            VALUATION_ANALYSIS_SKILL,
            PEER_COMPARISON_SKILL,
            EVENT_ANALYSIS_SKILL,
            VOLUME_LIQUIDITY_SKILL,
        ]:
            _default_registry.register(skill)

    return _default_registry