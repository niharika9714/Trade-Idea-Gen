from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data_access.document_parser import (
    parse_document,
)

from src.provenance.evidence import (
    Evidence,
    EvidenceBundle,
)


# ============================================================
# METADATA EXTRACTION
# ============================================================

def _detect_ticker(
    source: str,
) -> Optional[str]:

    filename = Path(source).name.upper()

    known_tickers = [
        "D05",
        "O39",
        "U11",
        "HSBA",
        "STAN",
    ]

    for ticker in known_tickers:

        if ticker in filename:
            return ticker

    return None


def _detect_event(
    source: str,
) -> Optional[str]:

    filename = Path(source).name.upper()

    import re

    match = re.search(
        r"([A-Z0-9]+-EVENT-\d+)",
        filename,
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# DOCUMENT → EVIDENCE
# ============================================================

def document_to_evidence(
    source_path: str,
    max_items: Optional[int] = None,
) -> EvidenceBundle:

    parsed = parse_document(
        source_path
    )

    bundle = EvidenceBundle()

    source = parsed["document"]
    document_type = parsed["document_type"]

    ticker = _detect_ticker(
        source
    )

    event_id = _detect_event(
        source
    )

    for item in parsed["evidence"]:

        evidence = Evidence(
            source_type=document_type,

            source=source,

            locator=item["locator"],

            content_type=item[
                "content_type"
            ],

            content=item.get(
                "text",
                ""
            ),

            ticker=ticker,

            event_id=event_id,

            source_system=(
                "synthetic_document_store"
            ),

            synthetic=True,

            metadata={
                key: value
                for key, value in item.items()
                if key not in {
                    "text",
                    "citation",
                    "locator",
                    "content_type",
                }
            },

            provenance={
                "document_type": document_type,
            },
        )

        bundle.add(
            evidence
        )

        if (
            max_items is not None
            and len(bundle.evidence)
            >= max_items
        ):
            break

    return bundle


# ============================================================
# DOCUMENT SEARCH → EVIDENCE
# ============================================================

def search_document_to_evidence(
    source_path: str,
    query: str,
    max_results: int = 10,
) -> EvidenceBundle:

    from src.data_access.document_parser import (
        search_document,
    )

    result = search_document(
        source_path,
        query,
        max_results=max_results,
    )

    bundle = EvidenceBundle()

    source = result["document"]

    ticker = _detect_ticker(
        source
    )

    event_id = _detect_event(
        source
    )

    document_type = (
        Path(source).suffix
        .lower()
        .replace(".", "")
    )

    for item in result["results"]:

        evidence = Evidence(
            source_type=document_type,

            source=source,

            locator=item["locator"],

            content_type=item[
                "content_type"
            ],

            content=item.get(
                "text",
                ""
            ),

            ticker=ticker,

            event_id=event_id,

            source_system=(
                "synthetic_document_store"
            ),

            synthetic=True,

            metadata={
                "query": query,
                "matched_terms": item.get(
                    "matched_terms",
                    [],
                ),
                "match_score": item.get(
                    "match_score",
                    0,
                ),
            },

            provenance={
                "retrieval_method": (
                    "deterministic_lexical_search"
                ),
            },
        )

        bundle.add(
            evidence
        )

    return bundle