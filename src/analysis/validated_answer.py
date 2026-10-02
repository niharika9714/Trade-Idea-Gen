from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.analysis.answer_validator import (
    AnswerValidationResult,
    validate_answer,
)
from src.provenance.evidence import EvidenceBundle


@dataclass
class ValidatedAnswer:
    """
    Answer that has passed deterministic validation.
    """

    answer: Any
    validation: AnswerValidationResult


class AnswerValidationError(ValueError):
    """Raised when an answer fails deterministic validation."""


def validate_and_accept_answer(
    answer: Any,
    evidence_bundle: EvidenceBundle,
) -> ValidatedAnswer:
    """
    Validate an LLM-generated answer against the authoritative
    EvidenceBundle.

    This is a fail-closed boundary.

    Invalid answers must never be returned as final answers.
    """

    if answer is None:
        raise AnswerValidationError(
            "Answer is required."
        )

    if evidence_bundle is None:
        raise AnswerValidationError(
            "Evidence bundle is required."
        )

    validation = validate_answer(
        answer=answer,
        evidence_bundle=evidence_bundle,
    )

    if not validation.valid:
        errors = getattr(
            validation,
            "errors",
            [],
        )

        raise AnswerValidationError(
            "Answer failed deterministic validation: "
            + "; ".join(str(error) for error in errors)
        )

    return ValidatedAnswer(
        answer=answer,
        validation=validation,
    )