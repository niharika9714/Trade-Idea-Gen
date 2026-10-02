from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ReasoningStep:
    """
    One explicit reasoning step.

    A reasoning step must identify:
    - what is being evaluated
    - what evidence supports it
    - what conclusion was derived
    """

    step_id: str
    description: str

    input_evidence_ids: list[str] = field(default_factory=list)
    input_citations: list[str] = field(default_factory=list)

    derived_from: list[str] = field(default_factory=list)

    conclusion: Optional[str] = None

    confidence: Optional[float] = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.input_evidence_ids = list(dict.fromkeys(self.input_evidence_ids))
        self.input_citations = list(dict.fromkeys(self.input_citations))
        self.derived_from = list(dict.fromkeys(self.derived_from))

        if self.confidence is not None:
            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError("confidence must be between 0 and 1")

    def to_dict(self):
        return {
            "step_id": self.step_id,
            "description": self.description,
            "input_evidence_ids": self.input_evidence_ids,
            "input_citations": self.input_citations,
            "derived_from": self.derived_from,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class ReasoningInput:
    """
    Controlled input to the reasoning layer.

    The reasoning layer receives:
    - original user query
    - analysis facts
    - derived metrics
    - evidence identifiers
    - citations
    """

    query: str

    facts: list[dict[str, Any]] = field(default_factory=list)

    derived_metrics: list[dict[str, Any]] = field(default_factory=list)

    evidence_ids: list[str] = field(default_factory=list)

    citations: list[str] = field(default_factory=list)

    entities: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")

        self.evidence_ids = list(dict.fromkeys(self.evidence_ids))
        self.citations = list(dict.fromkeys(self.citations))
        self.entities = list(dict.fromkeys(self.entities))

    def to_dict(self):
        return {
            "query": self.query,
            "facts": self.facts,
            "derived_metrics": self.derived_metrics,
            "evidence_ids": self.evidence_ids,
            "citations": self.citations,
            "entities": self.entities,
            "metadata": self.metadata,
        }


@dataclass
class ReasoningResult:
    """
    Output of the reasoning layer.

    This is intentionally NOT the final chatbot response.

    It is a structured reasoning artifact that can later be
    passed to an LLM response-generation layer.
    """

    query: str

    reasoning_steps: list[ReasoningStep] = field(default_factory=list)

    conclusion: Optional[str] = None

    supporting_evidence_ids: list[str] = field(default_factory=list)

    supporting_citations: list[str] = field(default_factory=list)

    limitations: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: ReasoningStep):
        if not isinstance(step, ReasoningStep):
            raise TypeError("step must be a ReasoningStep")

        self.reasoning_steps.append(step)

        self.supporting_evidence_ids.extend(step.input_evidence_ids)
        self.supporting_citations.extend(step.input_citations)

        self.supporting_evidence_ids = list(
            dict.fromkeys(self.supporting_evidence_ids)
        )

        self.supporting_citations = list(
            dict.fromkeys(self.supporting_citations)
        )

    def add_limitation(self, limitation: str):
        if limitation and limitation not in self.limitations:
            self.limitations.append(limitation)

    def to_dict(self):
        return {
            "query": self.query,
            "reasoning_steps": [
                step.to_dict()
                for step in self.reasoning_steps
            ],
            "conclusion": self.conclusion,
            "supporting_evidence_ids": self.supporting_evidence_ids,
            "supporting_citations": self.supporting_citations,
            "limitations": self.limitations,
            "metadata": self.metadata,
        }


def analysis_result_to_reasoning_input(
    query: str,
    analysis_result,
) -> ReasoningInput:
    """
    Convert the deterministic Evidence Analysis result into
    the controlled input expected by the reasoning layer.
    """

    facts = []
    derived_metrics = []

    evidence_ids = []
    citations = []
    entities = []

    for fact in analysis_result.facts:
        item = {
            "entity": fact.entity,
            "metric": fact.metric,
            "value": fact.value,
            "unit": fact.unit,
            "date": fact.date,
            "evidence_ids": list(fact.evidence_ids),
            "citations": list(fact.citations),
            "source_types": list(fact.source_types),
        }

        facts.append(item)

        evidence_ids.extend(fact.evidence_ids)
        citations.extend(fact.citations)

        if fact.entity:
            entities.append(fact.entity)

    for metric in analysis_result.derived_metrics:
        item = {
            "entity": metric.entity,
            "metric": metric.metric,
            "value": metric.value,
            "unit": metric.unit,
            "input_evidence_ids": list(metric.input_evidence_ids),
            "input_citations": list(metric.input_citations),
            "calculation": metric.calculation,
        }

        derived_metrics.append(item)

        evidence_ids.extend(metric.input_evidence_ids)
        citations.extend(metric.input_citations)

        if metric.entity:
            entities.append(metric.entity)

    return ReasoningInput(
        query=query,
        facts=facts,
        derived_metrics=derived_metrics,
        evidence_ids=list(dict.fromkeys(evidence_ids)),
        citations=list(dict.fromkeys(citations)),
        entities=list(dict.fromkeys(entities)),
    )


def validate_reasoning_result(
    result: ReasoningResult,
    allowed_evidence_ids: set[str],
    allowed_citations: set[str],
):
    """
    Validate that reasoning does not introduce unsupported
    evidence or citations.

    This is an important anti-hallucination boundary.
    """

    for evidence_id in result.supporting_evidence_ids:
        if evidence_id not in allowed_evidence_ids:
            raise ValueError(
                f"Reasoning references unknown evidence ID: {evidence_id}"
            )

    for citation in result.supporting_citations:
        if citation not in allowed_citations:
            raise ValueError(
                f"Reasoning references unknown citation: {citation}"
            )

    for step in result.reasoning_steps:

        for evidence_id in step.input_evidence_ids:
            if evidence_id not in allowed_evidence_ids:
                raise ValueError(
                    f"Reasoning step {step.step_id} references "
                    f"unknown evidence ID: {evidence_id}"
                )

        for citation in step.input_citations:
            if citation not in allowed_citations:
                raise ValueError(
                    f"Reasoning step {step.step_id} references "
                    f"unknown citation: {citation}"
                )

    return True