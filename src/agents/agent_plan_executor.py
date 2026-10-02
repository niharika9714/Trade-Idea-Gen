from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.agents.agent_plan_schema import AgentPlan
from src.agents.agent_plan_validator import validate_agent_plan
from src.data_access.retrieval_executor import execute_retrieval_plan
from src.data_access.retrieval_policy import (
    RetrievalPlan,
)
from src.provenance.evidence import EvidenceBundle
from src.agents.semantic_plan_adapter import (
    agent_plan_to_query_intent,
)

from src.data_access.retrieval_policy import (
    RetrievalPlan,
    build_retrieval_plan_from_intent,
)


@dataclass
class AgentPlanExecutionResult:
    """Result of executing an LLM-generated AgentPlan."""

    plan: AgentPlan
    retrieval_plan: RetrievalPlan
    evidence_bundle: EvidenceBundle


def _build_retrieval_plan(
    plan: AgentPlan,
) -> RetrievalPlan:
    """
    Convert the Qwen semantic AgentPlan into the canonical
    deterministic retrieval plan.

    Qwen determines semantic meaning.
    Deterministic policy determines executable retrieval.
    """

    query_intent = (
        agent_plan_to_query_intent(plan)
    )

    retrieval_plan = (
        build_retrieval_plan_from_intent(
            query_intent
        )
    )

    retrieval_plan.rationale.update(
        {
            "planner": "qwen3:8b",
            "semantic_intent": plan.intent,
            "entities": list(
                plan.entities
            ),
            "temporal_expression": (
                plan.temporal_expression
            ),
            "analytical_question": (
                plan.analytical_question
            ),
        }
    )

    return retrieval_plan

def execute_agent_plan(
    plan: AgentPlan,
    available_tool_names: set[str],
) -> AgentPlanExecutionResult:
    """
    Validate and execute an LLM-generated AgentPlan.

    The execution boundary is:

        AgentPlan
            ↓
        Validator
            ↓
        RetrievalPlan
            ↓
        Existing retrieval executor
            ↓
        EvidenceBundle
    """

    if plan is None:
        raise ValueError(
            "Agent plan is required."
        )

    validated_plan = validate_agent_plan(
        plan=plan,
        available_tool_names=available_tool_names,
    )

    retrieval_plan = _build_retrieval_plan(
        validated_plan
    )

    evidence_bundle = execute_retrieval_plan(
        plan=retrieval_plan,
        query=validated_plan.query,
    )

    if not isinstance(
        evidence_bundle,
        EvidenceBundle,
    ):
        raise TypeError(
            "Retrieval executor must return "
            "an EvidenceBundle."
        )

    return AgentPlanExecutionResult(
        plan=validated_plan,
        retrieval_plan=retrieval_plan,
        evidence_bundle=evidence_bundle,
    )