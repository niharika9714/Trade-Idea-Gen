"""
Step 4B - Answer Engine

Converts traceable ReasoningResult into AnswerResult.

The answer is constrained by:
    ReasoningResult
    Evidence IDs
    Citations

No unsupported factual claims are generated here.
"""

from __future__ import annotations

from src.analysis.answer_contract import (
    AnswerClaim,
    AnswerResult,
    AnswerSection,
    validate_answer_result,
)
from src.analysis.reasoning_contract import (
    ReasoningResult,
)


def build_answer(
    query: str,
    reasoning_result: ReasoningResult,
) -> AnswerResult:
    """
    Convert reasoning into a citation-backed answer.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError(
            "query must not be empty."
        )

    if reasoning_result is None:
        raise ValueError(
            "reasoning_result is required."
        )

    answer = AnswerResult(
        query=query,
    )

    # ---------------------------------------------------------
    # Executive summary
    # ---------------------------------------------------------

    conclusions = [
        step.conclusion
        for step in reasoning_result.reasoning_steps
        if step.conclusion
    ]

    if conclusions:
        answer.executive_summary = " ".join(
            conclusions[:3]
        )
    else:
        answer.executive_summary = (
            "No supported conclusion could be derived "
            "from the retrieved evidence."
        )

    # ---------------------------------------------------------
    # Main answer section
    # ---------------------------------------------------------

    section = AnswerSection(
        section_id="answer",
        title="Answer",
    )

    for index, step in enumerate(
        reasoning_result.reasoning_steps,
        start=1,
    ):
        claim = AnswerClaim(
            claim_id=f"claim-{index}",
            text=step.conclusion,
            evidence_ids=list(
                step.input_evidence_ids
            ),
            citations=list(
                step.input_citations
            ),
            claim_type="interpretation",
            metadata={
                "reasoning_step_id": step.step_id,
                "confidence": step.confidence,
            },
        )

        section.add_claim(
            claim
        )

    if section.claims:
        answer.add_section(
            section
        )

    # ---------------------------------------------------------
    # Citations
    # ---------------------------------------------------------

    for citation in reasoning_result.supporting_citations:
        if citation not in answer.overall_citations:
            answer.overall_citations.append(
                citation
            )

    # ---------------------------------------------------------
    # Limitations
    # ---------------------------------------------------------

    for limitation in reasoning_result.limitations:
        answer.add_limitation(
            limitation
        )

    return answer


def validate_answer(
    answer: AnswerResult,
    reasoning_result: ReasoningResult,
) -> bool:
    """
    Validate that every answer claim is backed by the
    reasoning evidence/citations.
    """

    return validate_answer_result(
        answer=answer,
        allowed_evidence_ids=set(
            reasoning_result.supporting_evidence_ids
        ),
        allowed_citations=set(
            reasoning_result.supporting_citations
        ),
        require_citation_for_claims=True,
    )


def render_answer(
    answer: AnswerResult,
) -> str:
    """
    Convert AnswerResult into the final console response.

    The executive summary is always shown, including when no
    supported answer is available. Claims are rendered only when
    they add information beyond the executive summary.
    """

    lines = []

    # ---------------------------------------------------------
    # Executive summary / no-answer condition
    # ---------------------------------------------------------
    executive_summary = (
        answer.executive_summary
        or "No answer available."
    )

    lines.append(executive_summary)

    # ---------------------------------------------------------
    # Answer claims
    # ---------------------------------------------------------
    for section in answer.sections:
        if section.title != "Answer":
            continue

        for claim in section.claims:
            claim_text = (
                claim.text
                or ""
            ).strip()

            if not claim_text:
                continue

            # Avoid printing the same statement twice when the
            # claim text is identical to the executive summary.
            if claim_text == executive_summary.strip():
                continue

            citation_text = ""

            if claim.citations:
                citation_text = (
                    " [Source: "
                    + "; ".join(
                        claim.citations
                    )
                    + "]"
                )

            lines.append(
                claim_text
                + citation_text
            )

    # ---------------------------------------------------------
    # Limitations
    # ---------------------------------------------------------
    if answer.limitations:
        lines.append("")
        lines.append(
            "Limitations:"
        )

        for limitation in answer.limitations:
            lines.append(
                f"- {limitation}"
            )

    return "\n".join(lines)