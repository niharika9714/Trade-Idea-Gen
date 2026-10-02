from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from src.provenance.evidence import Evidence, EvidenceBundle


@dataclass
class AnswerValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def raise_if_invalid(self) -> None:
        if not self.valid:
            raise ValueError(
                "Answer validation failed:\n"
                + "\n".join(
                    f"- {error}"
                    for error in self.errors
                )
            )


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _normalise_text(value: Any) -> str:
    return str(value or "").strip()


def _answer_to_dict(answer: Any) -> dict[str, Any]:
    """
    Convert supported AnswerResult / Pydantic / dataclass
    objects into a plain dictionary.
    """

    if answer is None:
        return {}

    if isinstance(answer, dict):
        return answer

    if hasattr(answer, "model_dump"):
        return answer.model_dump()

    if hasattr(answer, "dict"):
        return answer.dict()

    if hasattr(answer, "__dict__"):
        return dict(answer.__dict__)

    return {}


def _extract_claims(answer: Any) -> list[dict[str, Any]]:
    data = _answer_to_dict(answer)

    claims = data.get("claims")

    if isinstance(claims, list):
        return [
            claim
            for claim in claims
            if isinstance(claim, dict)
        ]

    sections = data.get("sections")

    if not isinstance(sections, list):
        return []

    extracted: list[dict[str, Any]] = []

    for section in sections:
        if not isinstance(section, dict):
            continue

        section_claims = section.get("claims")

        if not isinstance(section_claims, list):
            continue

        for claim in section_claims:
            if isinstance(claim, dict):
                extracted.append(claim)

    return extracted


def _extract_citations(claim: dict[str, Any]) -> list[str]:
    for field_name in (
        "citations",
        "citation",
        "evidence_citations",
        "sources",
    ):
        value = claim.get(field_name)

        if isinstance(value, str):
            return [value]

        if isinstance(value, list):
            return [
                str(item)
                for item in value
                if item
            ]

    return []


def _extract_claim_text(claim: dict[str, Any]) -> str:
    for field_name in (
        "text",
        "claim",
        "content",
        "statement",
    ):
        value = claim.get(field_name)

        if value:
            return str(value)

    return ""


def _build_evidence_indexes(
    bundle: EvidenceBundle,
) -> tuple[
    dict[str, Evidence],
    dict[str, Evidence],
    dict[str, Evidence],
]:
    by_citation: dict[str, Evidence] = {}
    by_id: dict[str, Evidence] = {}
    by_ticker: dict[str, Evidence] = {}

    for evidence in bundle:
        if not isinstance(evidence, Evidence):
            continue

        by_citation[evidence.citation] = evidence

        if evidence.evidence_id:
            by_id[evidence.evidence_id] = evidence

        if evidence.ticker:
            by_ticker.setdefault(
                evidence.ticker.upper(),
                evidence,
            )

    return (
        by_citation,
        by_id,
        by_ticker,
    )


def _extract_numbers(text: str) -> list[float]:
    """
    Extract ordinary decimal / integer numbers from answer text.

    Percentages are represented by their numeric value.
    Currency symbols are handled separately.
    """

    matches = re.findall(
        r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",
        text,
    )

    numbers: list[float] = []

    for match in matches:
        try:
            numbers.append(float(match))
        except ValueError:
            continue

    return numbers


def _number_supported(
    number: float,
    evidence_values: list[float],
    tolerance: float = 1e-4,
) -> bool:
    for value in evidence_values:
        if math.isclose(
            number,
            value,
            rel_tol=tolerance,
            abs_tol=tolerance,
        ):
            return True

    return False


def _supported_evidence_values(
    evidence: Evidence,
) -> list[float]:

    values: list[float] = []

    content = evidence.content

    if isinstance(content, dict):
        for field_name in (
            "value",
            "start_price",
            "end_price",
        ):
            value = content.get(field_name)

            if _is_number(value):
                values.append(float(value))

    return values


def _validate_currency(
    claim_text: str,
    evidence: list[Evidence],
    errors: list[str],
) -> None:

    currencies = {
        str(e.content.get("currency"))
        for e in evidence
        if isinstance(e.content, dict)
        and e.content.get("currency")
    }

    if not currencies:
        return

    text_upper = claim_text.upper()

    currency_symbols = {
        "$": "USD",
        "US$": "USD",
        "€": "EUR",
        "£": "GBP",
    }

    for symbol, currency_code in currency_symbols.items():
        if symbol in claim_text:
            if currency_code not in currencies:
                errors.append(
                    f"Answer uses currency '{currency_code}' "
                    f"but evidence supports {sorted(currencies)}"
                )

    for currency in currencies:
        if currency not in text_upper:
            continue

        # Explicitly supported.
        return

    # If another explicit ISO currency code appears,
    # reject it when unsupported.
    for code in (
        "USD",
        "EUR",
        "GBP",
        "SGD",
        "HKD",
        "JPY",
        "AUD",
    ):
        if re.search(
            rf"\b{code}\b",
            text_upper,
        ) and code not in currencies:
            errors.append(
                f"Answer uses currency '{code}' "
                f"but evidence supports {sorted(currencies)}"
            )


def _validate_dates(
    claim_text: str,
    evidence: list[Evidence],
    errors: list[str],
) -> None:

    dates: set[str] = set()

    for item in evidence:
        content = item.content

        if not isinstance(content, dict):
            continue

        for field_name in (
            "requested_start_date",
            "requested_end_date",
        ):
            value = content.get(field_name)

            if value:
                dates.add(str(value))

        for citation in (
            content.get("input_citations") or []
        ):
            match = re.search(
                r"trade_date=(\d{4}-\d{2}-\d{2})",
                str(citation),
            )

            if match:
                dates.add(match.group(1))

    if not dates:
        return

    # Calendar dates explicitly stated by Qwen must be
    # supported by the evidence.
    mentioned_dates = set(
        re.findall(
            r"\b20\d{2}-\d{2}-\d{2}\b",
            claim_text,
        )
    )

    unsupported = mentioned_dates - dates

    for date in sorted(unsupported):
        errors.append(
            f"Answer mentions unsupported date: {date}"
        )


def validate_answer(
    answer: Any,
    evidence_bundle: EvidenceBundle,
    *,
    reject_internal_evidence_ids: bool = True,
    require_citations: bool = True,
) -> AnswerValidationResult:

    errors: list[str] = []
    warnings: list[str] = []

    claims = _extract_claims(answer)

    if not claims:
        warnings.append(
            "Answer contains no structured claims"
        )

    (
        by_citation,
        by_id,
        _by_ticker,
    ) = _build_evidence_indexes(
        evidence_bundle
    )

    for index, claim in enumerate(claims):

        claim_text = _extract_claim_text(
            claim
        )

        citations = _extract_citations(
            claim
        )

        if require_citations and not citations:
            errors.append(
                f"Claim {index + 1} has no evidence citation"
            )
            continue

        claim_evidence: list[Evidence] = []

        for citation in citations:

            if (
                reject_internal_evidence_ids
                and citation.startswith("EV-")
            ):
                errors.append(
                    f"Claim {index + 1} exposes internal "
                    f"Evidence ID: {citation}"
                )
                continue

            evidence = by_citation.get(
                citation
            )

            if evidence is None:
                # Some answer schemas may return only an
                # evidence ID. This is intentionally rejected
                # for the user-facing answer.
                if citation in by_id:
                    errors.append(
                        f"Claim {index + 1} uses internal "
                        f"Evidence ID instead of citation: "
                        f"{citation}"
                    )
                else:
                    errors.append(
                        f"Claim {index + 1} cites evidence "
                        f"not present in the EvidenceBundle: "
                        f"{citation}"
                    )
                continue

            claim_evidence.append(
                evidence
            )

        if not claim_evidence:
            continue

        # Numeric support.
        answer_numbers = _extract_numbers(
            claim_text
        )

        evidence_values: list[float] = []

        for evidence in claim_evidence:
            evidence_values.extend(
                _supported_evidence_values(
                    evidence
                )
            )

        for number in answer_numbers:
            if not _number_supported(
                number,
                evidence_values,
            ):
                warnings.append(
                    f"Claim {index + 1} contains numeric "
                    f"value {number:g} that is not directly "
                    f"present in cited evidence"
                )

        _validate_currency(
            claim_text,
            claim_evidence,
            errors,
        )

        _validate_dates(
            claim_text,
            claim_evidence,
            errors,
        )

    return AnswerValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )