from __future__ import annotations

from typing import Any

from src.analysis.reasoning_contract import ReasoningResult


def build_answer_context(
    query: str,
    reasoning_result: ReasoningResult,
) -> dict[str, Any]:
    """
    Build the restricted context supplied to the answer-synthesis LLM.

    The answer LLM receives only deterministic reasoning output.
    It does not receive retrieval tools or unrestricted raw evidence.
    """

    if not query or not query.strip():
        raise ValueError("Query is required.")

    if reasoning_result is None:
        raise ValueError(
            "ReasoningResult is required."
        )

    reasoning_steps = []

    for step in reasoning_result.reasoning_steps:
        reasoning_steps.append(
            {
                "step_id": step.step_id,
                "description": step.description,
                "conclusion": step.conclusion,
                "evidence_ids": list(
                    step.input_evidence_ids
                ),
                "citations": list(
                    step.input_citations
                ),
                "confidence": step.confidence,
            }
        )

    return {
        "query": query,
        "conclusion": reasoning_result.conclusion,
        "reasoning_steps": reasoning_steps,
        "supporting_evidence_ids": list(
            reasoning_result.supporting_evidence_ids
        ),
        "supporting_citations": list(
            reasoning_result.supporting_citations
        ),
        "limitations": list(
            reasoning_result.limitations
        ),
    }