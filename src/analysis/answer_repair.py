from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.analysis.answer_validator import (
    AnswerValidationResult,
    validate_answer,
)
from src.provenance.evidence import EvidenceBundle


@dataclass
class AnswerRepairAttempt:
    """
    One answer generation/validation attempt.
    """

    attempt_number: int
    answer: Any
    validation: AnswerValidationResult


@dataclass
class AnswerRepairResult:
    """
    Final result of answer generation + validation + repair.
    """

    answer: Any | None
    accepted: bool
    attempts: list[AnswerRepairAttempt]
    final_validation: AnswerValidationResult | None


class AnswerRepairError(ValueError):
    """
    Raised when the answer cannot be made valid within
    the configured repair limit.
    """


def _validation_errors(
    validation: AnswerValidationResult,
) -> list[str]:
    """
    Extract validation errors without assuming a specific
    internal representation beyond the existing validator.
    """

    errors = getattr(
        validation,
        "errors",
        [],
    )

    if errors is None:
        return []

    return [
        str(error)
        for error in errors
    ]


def build_repair_instruction(
    validation: AnswerValidationResult,
) -> str:
    """
    Convert deterministic validator failures into a concise
    instruction for the answer-generation model.
    """

    errors = _validation_errors(validation)

    if not errors:
        return (
            "The previous answer failed validation. "
            "Regenerate the answer using only the supplied "
            "evidence and citations."
        )

    numbered_errors = "\n".join(
        f"{index}. {error}"
        for index, error in enumerate(
            errors,
            start=1,
        )
    )

    return f"""
The previous answer failed deterministic validation.

You MUST repair the answer.

Validation errors:

{numbered_errors}

Repair rules:

1. Use only information supported by the supplied evidence.
2. Do not invent facts or numbers.
3. Do not perform calculations yourself when a deterministic
   analytical result is available.
4. Use the exact user-facing evidence citations supplied
   by the evidence context.
5. Never expose internal EV-* evidence IDs.
6. Use the currency supported by the evidence.
7. Preserve the user's requested date range unless the evidence
   explicitly requires describing the first/last available
   observation.
8. Remove unsupported claims rather than guessing.
9. Return the same structured answer format.
""".strip()


def repair_answer(
    *,
    initial_answer: Any,
    evidence_bundle: EvidenceBundle,
    regenerate: Callable[[Any, str], Any],
    max_attempts: int = 2,
) -> AnswerRepairResult:
    """
    Validate an answer and, if necessary, ask the answer generator
    to repair it.

    Parameters
    ----------
    initial_answer:
        First answer produced by the answer LLM.

    evidence_bundle:
        Authoritative evidence used to validate the answer.

    regenerate:
        Callable receiving:

            previous_answer
            repair_instruction

        and returning a new structured answer.

    max_attempts:
        Maximum total answer attempts, including the initial answer.

    Returns
    -------
    AnswerRepairResult

    Raises
    ------
    AnswerRepairError
        If validation still fails after max_attempts.
    """

    if initial_answer is None:
        raise ValueError(
            "Initial answer is required."
        )

    if evidence_bundle is None:
        raise ValueError(
            "Evidence bundle is required."
        )

    if regenerate is None:
        raise ValueError(
            "Answer regeneration callable is required."
        )

    if max_attempts < 1:
        raise ValueError(
            "max_attempts must be at least 1."
        )

    attempts: list[AnswerRepairAttempt] = []

    current_answer = initial_answer

    for attempt_number in range(
        1,
        max_attempts + 1,
    ):
        validation = validate_answer(
            answer=current_answer,
            evidence_bundle=evidence_bundle,
        )

        attempt = AnswerRepairAttempt(
            attempt_number=attempt_number,
            answer=current_answer,
            validation=validation,
        )

        attempts.append(attempt)

        if validation.valid:
            return AnswerRepairResult(
                answer=current_answer,
                accepted=True,
                attempts=attempts,
                final_validation=validation,
            )

        if attempt_number >= max_attempts:
            break

        repair_instruction = (
            build_repair_instruction(
                validation
            )
        )

        current_answer = regenerate(
            current_answer,
            repair_instruction,
        )

        if current_answer is None:
            raise AnswerRepairError(
                "Answer regeneration returned no answer."
            )

    final_validation = attempts[-1].validation

    raise AnswerRepairError(
        "Answer failed deterministic validation "
        f"after {max_attempts} attempts: "
        + "; ".join(
            _validation_errors(final_validation)
        )
    )