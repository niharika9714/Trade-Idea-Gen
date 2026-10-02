from src.analysis.skill_contract import SkillContext
from src.analysis.skill_executor import SkillExecutor
from src.analysis.skill_selector import (
    select_skills,
)

from src.agents.skill_agent_contract import (
    SkillDecision,
    SkillExecutionResult,
)


class SkillAgentExecutor:

    def __init__(self):

        self.skill_executor = SkillExecutor()

    def select_skills(
        self,
        query_intent,
    ) -> SkillDecision:

        selection = select_skills(
            query_intent
        )

        return SkillDecision(
            skill_names=selection.skills,
            reasoning=selection.rationale,
            confidence=1.0
            if selection.skills
            else 0.0,
        )

    def execute(
        self,
        query: str,
        query_intent,
        evidence_bundle,
    ):

        decision = self.select_skills(
            query_intent
        )

        context = SkillContext(
            query=query,
            query_intent=query_intent,
            evidence_bundle=evidence_bundle,
        )

        results = []

        for skill_name in decision.skill_names:

            try:

                result = (
                    self.skill_executor.execute(
                        skill_name,
                        context,
                    )
                )

                results.append(
                    SkillExecutionResult(
                        skill_name=skill_name,
                        status=result.status,
                        evidence_ids=(
                            result.evidence_ids
                        ),
                        citations=(
                            result.citations
                        ),
                        result=result,
                    )
                )

            except Exception as exc:

                results.append(
                    SkillExecutionResult(
                        skill_name=skill_name,
                        status="failed",
                        error=str(exc),
                    )
                )

        return decision, results