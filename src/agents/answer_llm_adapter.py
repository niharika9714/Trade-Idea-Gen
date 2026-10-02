from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ollama import chat

from src.analysis.answer_contract import (
    AnswerClaim,
    AnswerResult,
    AnswerSection,
)
from src.analysis.answer_engine import build_answer
from src.analysis.reasoning_contract import ReasoningResult
from src.agents.answer_output_schema import AnswerOutput
from src.agents.answer_prompt import (
    SYSTEM_PROMPT,
    build_answer_prompt,
)


OLLAMA_MODEL = "qwen3:8b"


class AnswerLLMAdapter(ABC):
    """
    Interface for the answer-synthesis LLM.

    The rest of the application depends only on this interface.
    """

    @abstractmethod
    def generate_answer(
        self,
        query: str,
        reasoning_result: ReasoningResult,
        answer_context: dict[str, Any],
    ) -> AnswerResult:
        raise NotImplementedError


class MockAnswerLLMAdapter(AnswerLLMAdapter):
    """
    Deterministic adapter used by unit tests.
    """

    def generate_answer(
        self,
        query: str,
        reasoning_result: ReasoningResult,
        answer_context: dict[str, Any],
    ) -> AnswerResult:

        return build_answer(
            query=query,
            reasoning_result=reasoning_result,
        )


class OllamaAnswerLLMAdapter(AnswerLLMAdapter):
    """
    Local Ollama answer-synthesis adapter.

    Model:
        qwen3:8b

    Responsibilities:
        - send reasoning context to Qwen
        - request structured output
        - validate structured output with Pydantic
        - convert it into the internal AnswerResult contract

    This adapter does NOT retrieve data and does NOT execute tools.
    """

    def __init__(
        self,
        model: str = OLLAMA_MODEL,
        temperature: float = 0.0,
    ):
        if not model or not model.strip():
            raise ValueError(
                "Ollama model is required."
            )

        self.model = model
        self.temperature = temperature

    def generate_answer(
        self,
        query: str,
        reasoning_result: ReasoningResult,
        answer_context: dict[str, Any],
    ) -> AnswerResult:

        prompt = build_answer_prompt(
            query=query,
            answer_context=answer_context,
        )

        response = chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            format=AnswerOutput.model_json_schema(),
            options={
                "temperature": self.temperature,
            },
        )

        content = response.message.content

        if not content:
            raise ValueError(
                "Ollama returned an empty answer."
            )

        output = AnswerOutput.model_validate_json(
            content
        )

        answer = self._convert_to_answer_result(
            query=query,
            output=output,
        )
        
        self.validate_provenance(
            answer=answer,
            reasoning_result=reasoning_result,
        )
        
        return answer

    @staticmethod
    def _convert_to_answer_result(
        query: str,
        output: AnswerOutput,
    ) -> AnswerResult:
        """
        Convert the external Qwen output schema into the internal
        AnswerResult contract.
        """

        answer = AnswerResult(
            query=query,
            executive_summary=output.executive_summary,
        )

        for section_output in output.sections:

            section = AnswerSection(
                section_id=section_output.section_id,
                title=section_output.title,
            )

            for claim_output in section_output.claims:
                claim_type_aliases = {
                    "fact": "factual",
                    "interpretive": "interpretation",
                    }

                claim_type = claim_type_aliases.get(
                    claim_output.claim_type,
                    claim_output.claim_type,
                )

                claim = AnswerClaim(
                    claim_id=claim_output.claim_id,
                    text=claim_output.text,
                    evidence_ids=list(
                        claim_output.evidence_ids
                    ),
                    citations=list(
                        claim_output.citations
                    ),
                    claim_type=claim_type,
                    entity=claim_output.entity,
                    metric=claim_output.metric,
                )

                section.add_claim(claim)

            answer.add_section(section)

        for citation in output.overall_citations:
            if citation not in answer.overall_citations:
                answer.overall_citations.append(
                    citation
                )

        for limitation in output.limitations:
            answer.add_limitation(
                limitation
            )

        return answer

    @staticmethod
    def validate_provenance(
        answer: AnswerResult,
        reasoning_result: ReasoningResult,
    ) -> None:
        """
        Ensure that the LLM only references evidence and citations
        supplied by the deterministic reasoning layer.
        """

        allowed_evidence_ids = set(
            reasoning_result.supporting_evidence_ids
        )

        allowed_citations = set(
            reasoning_result.supporting_citations
        )

        for section in answer.sections:

            for claim in section.claims:

                for evidence_id in claim.evidence_ids:

                    if evidence_id not in allowed_evidence_ids:
                        raise ValueError(
                            "LLM generated unsupported "
                            f"evidence ID: {evidence_id}"
                        )

                for citation in claim.citations:

                    if citation not in allowed_citations:
                        raise ValueError(
                            "LLM generated unsupported "
                            f"citation: {citation}"
                        )

        for citation in answer.overall_citations:

            if citation not in allowed_citations:
                raise ValueError(
                    "LLM generated unsupported "
                    f"overall citation: {citation}"
                )