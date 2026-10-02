from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from src.provenance.evidence import (
    Evidence,
    EvidenceBundle,
)


def api_response_to_evidence(
    response: Dict[str, Any],
    filename: str,
    ticker: Optional[str] = None,
) -> EvidenceBundle:

    bundle = EvidenceBundle()

    # --------------------------------------------------------
    # Detect ticker
    # --------------------------------------------------------

    if not ticker:

        filename_upper = filename.upper()

        for candidate in [
            "D05",
            "O39",
            "U11",
            "HSBA",
            "STAN",
        ]:

            if candidate in filename_upper:
                ticker = candidate
                break

    # --------------------------------------------------------
    # Determine response type
    # --------------------------------------------------------

    response_type = response.get(
        "response_type",
        response.get(
            "type",
            "api_response",
        ),
    )

    # --------------------------------------------------------
    # Provenance from source API
    # --------------------------------------------------------

    source_provenance = response.get(
        "provenance",
        {},
    )

    evidence = Evidence(
        source_type="internal_api",

        source=(
            "data/internal_api/responses/"
            + filename
        ),

        locator=(
            f"response_type={response_type}"
        ),

        content_type="api_response",

        content=response,

        ticker=ticker,

        source_system=(
            source_provenance.get(
                "source_system",
                "Synthetic Internal Pricing Engine",
            )
        ),

        synthetic=source_provenance.get(
            "synthetic",
            True,
        ),

        metadata={
            "filename": filename,
            "response_type": response_type,
        },

        provenance={
            **source_provenance,

            "retrieval_method": (
                "direct_internal_api_response"
            ),
        },
    )

    bundle.add(
        evidence
    )

    return bundle