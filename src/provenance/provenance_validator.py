from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.provenance.evidence import Evidence, EvidenceBundle


SUPPORTED_CALCULATIONS = {
    "price_change",
    "return",
}

REQUIRED_CONTENT_FIELDS = {
    "ticker",
    "metric",
    "requested_start_date",
    "requested_end_date",
    "start_price",
    "end_price",
    "value",
    "currency",
    "exchange",
    "instrument_type",
    "instrument_id",
    "calculation",
    "input_citations",
}

REQUIRED_PROVENANCE_FIELDS = {
    "source_system",
    "retrieval_method",
    "calculation_engine",
    "source_type",
    "source",
    "locator",
    "content_type",
    "synthetic",
    "input_citations",
}


@dataclass
class ProvenanceValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def raise_if_invalid(self) -> None:
        if not self.valid:
            raise ValueError(
                "Provenance validation failed:\n"
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


def _validate_price_change(
    content: dict[str, Any],
    tolerance: float,
) -> list[str]:

    errors: list[str] = []

    start_price = content.get("start_price")
    end_price = content.get("end_price")
    value = content.get("value")

    if not (
        _is_number(start_price)
        and _is_number(end_price)
        and _is_number(value)
    ):
        return errors

    expected = float(end_price) - float(start_price)

    if not math.isclose(
        float(value),
        expected,
        rel_tol=tolerance,
        abs_tol=tolerance,
    ):
        errors.append(
            "price_change value does not match "
            "end_price - start_price"
        )

    calculation = str(
        content.get("calculation", "")
    )

    expected_calculation = (
        f"{end_price} - {start_price}"
    )

    if calculation != expected_calculation:
        errors.append(
            "price_change calculation formula does not "
            "match the recorded start/end prices"
        )

    return errors


def _validate_return(
    content: dict[str, Any],
    tolerance: float,
) -> list[str]:

    errors: list[str] = []

    start_price = content.get("start_price")
    end_price = content.get("end_price")
    value = content.get("value")

    if not (
        _is_number(start_price)
        and _is_number(end_price)
        and _is_number(value)
    ):
        return errors

    if float(start_price) == 0:
        errors.append(
            "return calculation has zero start_price"
        )
        return errors

    expected = (
        float(end_price) - float(start_price)
    ) / float(start_price)

    if not math.isclose(
        float(value),
        expected,
        rel_tol=tolerance,
        abs_tol=tolerance,
    ):
        errors.append(
            "return value does not match "
            "(end_price - start_price) / start_price"
        )

    calculation = str(
        content.get("calculation", "")
    )

    expected_calculation = (
        f"({end_price} - {start_price}) / "
        f"{start_price}"
    )

    if calculation != expected_calculation:
        errors.append(
            "return calculation formula does not "
            "match the recorded start/end prices"
        )

    return errors


def validate_calculation_evidence(
    evidence: Evidence,
    tolerance: float = 1e-9,
) -> ProvenanceValidationResult:

    errors: list[str] = []
    warnings: list[str] = []

    if evidence.source_type != "calculation":
        errors.append(
            "Evidence source_type must be 'calculation'"
        )

    if evidence.content_type != "derived_metric":
        errors.append(
            "Calculation evidence content_type must be "
            "'derived_metric'"
        )

    content = evidence.content

    if not isinstance(content, dict):
        errors.append(
            "Calculation evidence content must be a dictionary"
        )
        return ProvenanceValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings,
        )

    missing_content = sorted(
        REQUIRED_CONTENT_FIELDS - set(content.keys())
    )

    for field_name in missing_content:
        errors.append(
            f"Missing required calculation content field: "
            f"{field_name}"
        )

    metric = content.get("metric")

    if metric not in SUPPORTED_CALCULATIONS:
        errors.append(
            f"Unsupported calculation metric: {metric}"
        )

    ticker = content.get("ticker")

    if not ticker:
        errors.append(
            "Calculation evidence is missing ticker"
        )

    if evidence.ticker != ticker:
        errors.append(
            "Evidence ticker does not match content ticker"
        )

    for field_name in (
        "requested_start_date",
        "requested_end_date",
        "currency",
        "exchange",
        "instrument_type",
        "instrument_id",
        "calculation",
    ):
        value = content.get(field_name)

        if value is None or value == "":
            errors.append(
                f"Calculation content field '{field_name}' "
                "must not be empty"
            )

    for field_name in (
        "start_price",
        "end_price",
        "value",
    ):
        value = content.get(field_name)

        if not _is_number(value):
            errors.append(
                f"Calculation content field '{field_name}' "
                "must be a finite number"
            )

    input_citations = content.get(
        "input_citations"
    )

    if not isinstance(input_citations, list):
        errors.append(
            "input_citations must be a list"
        )
        input_citations = []

    elif len(input_citations) < 2:
        errors.append(
            "Calculation evidence must contain at least "
            "two input citations"
        )

    for citation in input_citations:
        if not isinstance(citation, str):
            errors.append(
                "Every input citation must be a string"
            )
            continue

        if not citation.startswith(
            "market.db#daily_prices."
        ):
            errors.append(
                "Calculation input citation must reference "
                "market.db#daily_prices"
            )

    provenance = evidence.provenance

    if not isinstance(provenance, dict):
        errors.append(
            "Calculation evidence provenance must be a dictionary"
        )
        provenance = {}

    missing_provenance = sorted(
        REQUIRED_PROVENANCE_FIELDS
        - set(provenance.keys())
    )

    for field_name in missing_provenance:
        errors.append(
            f"Missing required provenance field: "
            f"{field_name}"
        )

    expected_provenance = {
        "source_type": "calculation",
        "source": "market.db",
        "content_type": "derived_metric",
        "retrieval_method": "deterministic_calculation",
        "calculation_engine": "python",
    }

    for field_name, expected_value in (
        expected_provenance.items()
    ):
        actual_value = provenance.get(field_name)

        if actual_value != expected_value:
            errors.append(
                f"Provenance field '{field_name}' must be "
                f"'{expected_value}', got '{actual_value}'"
            )

    provenance_inputs = provenance.get(
        "input_citations"
    )

    if provenance_inputs != input_citations:
        errors.append(
            "Provenance input_citations do not match "
            "content input_citations"
        )

    currency_source = provenance.get(
        "currency_source"
    )

    if currency_source != (
        "market.db#instruments.currency"
    ):
        errors.append(
            "Currency provenance must reference "
            "market.db#instruments.currency"
        )

    instrument_source = provenance.get(
        "instrument_source"
    )

    if instrument_source != "market.db#instruments":
        errors.append(
            "Instrument provenance must reference "
            "market.db#instruments"
        )

    if metric == "price_change":
        errors.extend(
            _validate_price_change(
                content,
                tolerance,
            )
        )

    elif metric == "return":
        errors.extend(
            _validate_return(
                content,
                tolerance,
            )
        )

    return ProvenanceValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_calculation_bundle(
    bundle: EvidenceBundle,
    tolerance: float = 1e-9,
) -> ProvenanceValidationResult:

    errors: list[str] = []
    warnings: list[str] = []

    calculation_count = 0

    for evidence in bundle:

        if not isinstance(evidence, Evidence):
            errors.append(
                "EvidenceBundle contains a non-Evidence object"
            )
            continue

        if evidence.source_type != "calculation":
            continue

        calculation_count += 1

        result = validate_calculation_evidence(
            evidence,
            tolerance=tolerance,
        )

        errors.extend(
            result.errors
        )

        warnings.extend(
            result.warnings
        )

    if calculation_count == 0:
        warnings.append(
            "EvidenceBundle contains no calculation evidence"
        )

    return ProvenanceValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )