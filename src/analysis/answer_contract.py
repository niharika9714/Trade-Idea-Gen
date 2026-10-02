from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AnswerClaim:
    """
    One factual or derived claim in the final research answer.

    Every material claim must point to evidence or a declared
    derived metric.
    """

    claim_id: str
    text: str

    evidence_ids: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)

    claim_type: str = "factual"
    entity: Optional[str] = None
    metric: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.claim_id:
            raise ValueError("claim_id is required")

        if not self.text or not self.text.strip():
            raise ValueError("claim text must not be empty")

        allowed_types = {
            "factual",
            "derived",
            "interpretation",
            "limitation",
        }

        if self.claim_type not in allowed_types:
            raise ValueError(
                f"Unsupported claim_type: {self.claim_type}"
            )

        self.evidence_ids = list(
            dict.fromkeys(self.evidence_ids)
        )

        self.citations = list(
            dict.fromkeys(self.citations)
        )

    def to_dict(self):
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "evidence_ids": self.evidence_ids,
            "citations": self.citations,
            "claim_type": self.claim_type,
            "entity": self.entity,
            "metric": self.metric,
            "metadata": self.metadata,
        }


@dataclass
class AnswerSection:
    """
    A logical section of the final investment research answer.
    """

    section_id: str
    title: str

    claims: list[AnswerClaim] = field(default_factory=list)

    def add_claim(self, claim: AnswerClaim):
        if not isinstance(claim, AnswerClaim):
            raise TypeError("claim must be an AnswerClaim")

        self.claims.append(claim)

    def to_dict(self):
        return {
            "section_id": self.section_id,
            "title": self.title,
            "claims": [
                claim.to_dict()
                for claim in self.claims
            ],
        }


@dataclass
class AnswerResult:
    """
    Structured final answer contract.

    This is the object that the future LLM response-generation
    layer must produce.
    """

    query: str

    sections: list[AnswerSection] = field(default_factory=list)

    executive_summary: Optional[str] = None

    overall_citations: list[str] = field(default_factory=list)

    limitations: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def add_section(self, section: AnswerSection):
        if not isinstance(section, AnswerSection):
            raise TypeError("section must be an AnswerSection")

        self.sections.append(section)

    def add_limitation(self, limitation: str):
        if limitation and limitation not in self.limitations:
            self.limitations.append(limitation)

    def collect_claims(self):
        claims = []

        for section in self.sections:
            claims.extend(section.claims)

        return claims

    def collect_evidence_ids(self):
        evidence_ids = []

        for claim in self.collect_claims():
            evidence_ids.extend(claim.evidence_ids)

        return list(dict.fromkeys(evidence_ids))

    def collect_citations(self):
        citations = []

        citations.extend(self.overall_citations)

        for claim in self.collect_claims():
            citations.extend(claim.citations)

        return list(dict.fromkeys(citations))

    def to_dict(self):
        return {
            "query": self.query,
            "executive_summary": self.executive_summary,
            "sections": [
                section.to_dict()
                for section in self.sections
            ],
            "overall_citations": self.overall_citations,
            "limitations": self.limitations,
            "metadata": self.metadata,
        }


def validate_answer_result(
    answer: AnswerResult,
    allowed_evidence_ids: set[str],
    allowed_citations: set[str],
    require_citation_for_claims: bool = True,
):
    """
    Validate the final answer against the evidence boundary.

    Rules:
    1. Every referenced evidence ID must exist.
    2. Every referenced citation must exist.
    3. Material factual/derived/interpretation claims must
       have supporting evidence when citation enforcement is on.
    """

    if not isinstance(answer, AnswerResult):
        raise TypeError("answer must be an AnswerResult")

    if not answer.query.strip():
        raise ValueError("Answer query cannot be empty")

    # Validate overall citations.
    for citation in answer.overall_citations:
        if citation not in allowed_citations:
            raise ValueError(
                f"Answer references unknown citation: {citation}"
            )

    # Validate every claim.
    for claim in answer.collect_claims():

        for evidence_id in claim.evidence_ids:
            if evidence_id not in allowed_evidence_ids:
                raise ValueError(
                    f"Claim {claim.claim_id} references "
                    f"unknown evidence ID: {evidence_id}"
                )

        for citation in claim.citations:
            if citation not in allowed_citations:
                raise ValueError(
                    f"Claim {claim.claim_id} references "
                    f"unknown citation: {citation}"
                )

        if require_citation_for_claims:

            requires_support = claim.claim_type in {
                "factual",
                "derived",
                "interpretation",
            }

            if requires_support:

                if not claim.evidence_ids:
                    raise ValueError(
                        f"Claim {claim.claim_id} has no supporting "
                        f"evidence IDs"
                    )

                if not claim.citations:
                    raise ValueError(
                        f"Claim {claim.claim_id} has no supporting "
                        f"citations"
                    )

    return True


def build_answer_from_reasoning(
    query: str,
    reasoning_result,
    title: str = "Research Analysis",
):
    """
    Convert a ReasoningResult into the AnswerResult structure.

    This does not generate prose automatically. It establishes
    the evidence-bound structure that a future LLM can populate.
    """

    answer = AnswerResult(
        query=query
    )

    section = AnswerSection(
        section_id="SEC-001",
        title=title,
    )

    for index, step in enumerate(
        reasoning_result.reasoning_steps,
        start=1,
    ):
        if step.conclusion:

            claim = AnswerClaim(
                claim_id=f"CLM-{index:03d}",
                text=step.conclusion,
                evidence_ids=step.input_evidence_ids,
                citations=step.input_citations,
                claim_type="interpretation",
            )

            section.add_claim(claim)

    answer.add_section(section)

    answer.limitations.extend(
        reasoning_result.limitations
    )

    answer.overall_citations = list(
        dict.fromkeys(
            reasoning_result.supporting_citations
        )
    )

    return answer