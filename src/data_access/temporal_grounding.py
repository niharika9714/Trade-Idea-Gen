from __future__ import annotations

import calendar
import re
from datetime import date, datetime
from typing import Any


_MONTHS = {
    month.lower(): number
    for number, month in enumerate(calendar.month_name)
    if month
}


def ground_temporal_expression(
    temporal_expression: str | None,
    *,
    reference_date: date | None = None,
) -> dict[str, Any] | None:
    """
    Convert an LLM-extracted temporal expression into deterministic
    retrieval boundaries.

    Semantic interpretation belongs to the LLM planner.
    This function only canonicalizes supported temporal expressions
    into exact calendar dates.
    """

    if temporal_expression is None:
        return None

    expression = temporal_expression.strip()

    if not expression:
        return None

    reference_date = (
        reference_date
        or datetime.now().date()
    )

    # ---------------------------------------------------------
    # Month + year
    #
    # Example:
    # January 2024
    # ---------------------------------------------------------

    month_year_match = re.fullmatch(
        r"([A-Za-z]+)\s+(\d{4})",
        expression,
    )

    if month_year_match:
        month_name = (
            month_year_match
            .group(1)
            .lower()
        )

        year = int(
            month_year_match.group(2)
        )

        month = _MONTHS.get(
            month_name
        )

        if month is None:
            raise ValueError(
                "Unsupported month in temporal "
                f"expression: {expression}"
            )

        last_day = calendar.monthrange(
            year,
            month,
        )[1]

        return {
            "type": "absolute",
            "start_date": date(
                year,
                month,
                1,
            ).isoformat(),
            "end_date": date(
                year,
                month,
                last_day,
            ).isoformat(),
            "source_expression": expression,
        }

    # ---------------------------------------------------------
    # Quarter + year
    #
    # Example:
    # Q1 2024
    # ---------------------------------------------------------

    quarter_match = re.fullmatch(
        r"[Qq]([1-4])\s+(\d{4})",
        expression,
    )

    if quarter_match:
        quarter = int(
            quarter_match.group(1)
        )

        year = int(
            quarter_match.group(2)
        )

        start_month = (
            (quarter - 1) * 3 + 1
        )

        end_month = (
            start_month + 2
        )

        end_day = calendar.monthrange(
            year,
            end_month,
        )[1]

        return {
            "type": "absolute",
            "start_date": date(
                year,
                start_month,
                1,
            ).isoformat(),
            "end_date": date(
                year,
                end_month,
                end_day,
            ).isoformat(),
            "source_expression": expression,
        }

    # ---------------------------------------------------------
    # Explicit year
    #
    # Example:
    # 2024
    # ---------------------------------------------------------

    year_match = re.fullmatch(
        r"\d{4}",
        expression,
    )

    if year_match:
        year = int(expression)

        return {
            "type": "absolute",
            "start_date": date(
                year,
                1,
                1,
            ).isoformat(),
            "end_date": date(
                year,
                12,
                31,
            ).isoformat(),
            "source_expression": expression,
        }

    raise ValueError(
        "Temporal expression was understood by the "
        "semantic planner but cannot yet be deterministically "
        f"grounded: {expression!r}"
    )