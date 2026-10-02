from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from src.provenance.evidence import (
    Evidence,
    EvidenceBundle,
)


def sql_rows_to_evidence(
    rows: Iterable[Dict[str, Any]],
    table_name: str,
    query: str,
    ticker: Optional[str] = None,
    locator_field: Optional[str] = None,
) -> EvidenceBundle:

    bundle = EvidenceBundle()

    for index, row in enumerate(rows):

        # ----------------------------------------------------
        # Determine locator
        # ----------------------------------------------------

        if (
            locator_field
            and locator_field in row
        ):

            locator = (
                f"{table_name}"
                f".{locator_field}="
                f"{row[locator_field]}"
            )

        else:

            locator = (
                f"{table_name}"
                f".row={index}"
            )

        # ----------------------------------------------------
        # Try to infer ticker
        # ----------------------------------------------------

        row_ticker = ticker

        if not row_ticker:

            possible_ticker = row.get(
                "ticker"
            )

            if possible_ticker:
                row_ticker = str(
                    possible_ticker
                ).upper()

        # ----------------------------------------------------
        # Evidence
        # ----------------------------------------------------

        evidence = Evidence(
            source_type="sql",

            source="market.db",

            locator=locator,

            content_type="database_record",

            content=dict(row),

            ticker=row_ticker,

            source_system="synthetic_market_database",

            synthetic=True,

            metadata={
                "table": table_name,
                "query": query,
                "row_number": index,
            },

            provenance={
                "retrieval_method": (
                    "direct_sql_query"
                ),
                "table": table_name,
                "query": query,
            },
        )

        bundle.add(
            evidence
        )

    return bundle