from src.analysis.skill_contract import SkillContext
from src.analysis.skill_registry import (
    get_skill_registry,
)


class SkillExecutor:

    def __init__(self):
        self.registry = get_skill_registry()

    def execute(
        self,
        skill_name: str,
        context: SkillContext,
    ):

        skill = self.registry.get(
            skill_name
        )

        result = skill.execute_function(
            context
        )

        return result

    def execute_many(
        self,
        skill_names: list[str],
        context: SkillContext,
    ):

        results = []

        for skill_name in skill_names:

            result = self.execute(
                skill_name,
                context,
            )

            results.append(result)

        return results