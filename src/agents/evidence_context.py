from __future__ import annotations

from typing import Any

from src.provenance.evidence import Evidence, EvidenceBundle


MAX_CONTENT_PER_EVIDENCE = 1200
MAX_TOTAL_CONTEXT = 8000
MAX_EVIDENCE_ITEMS = 12


def _safe_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (dict, list, tuple)):
        return str(value)

    return str(value)


def _extract_content(evidence: Evidence) -> str:
    content = evidence.content

    if isinstance(content, dict):

        # Prefer the fields most useful for reasoning.
        preferred_fields = (
            "text",
            "content",
            "value",
            "close_price",
            "adjusted_close",
            "daily_return",
            "trade_date",
            "report_date",
            "ticker",
        )

        parts = []

        for field in preferred_fields:

            if field in content:

                value = _safe_value(
                    content[field]
                )

                if value:
                    parts.append(
                        f"{field}={value}"
                    )

        if parts:
            return " | ".join(parts)

        return str(content)

    return _safe_value(content)


def _format_single_evidence(
    evidence: Evidence,
) -> str:

    content = _extract_content(evidence)

    if len(content) > MAX_CONTENT_PER_EVIDENCE:
        content = (
            content[:MAX_CONTENT_PER_EVIDENCE]
            + "..."
        )

    lines = [
        f"Evidence ID: {evidence.evidence_id}",
        f"Source type: {evidence.source_type}",
        f"Source: {evidence.source}",
        f"Locator: {evidence.locator}",
        f"Citation: {evidence.citation}",
    ]

    if evidence.ticker:
        lines.append(
            f"Ticker: {evidence.ticker}"
        )

    if evidence.event_id:
        lines.append(
            f"Event: {evidence.event_id}"
        )

    if evidence.content_type:
        lines.append(
            f"Content type: {evidence.content_type}"
        )

    lines.append(
        f"Content: {content}"
    )

    return "\n".join(lines)


def build_evidence_context(
    evidence_bundle: EvidenceBundle,
) -> str:
    """
    Build a compact reasoning context for Qwen.

    IMPORTANT:
    This does NOT modify or truncate the original EvidenceBundle.

    The full EvidenceBundle remains available to deterministic
    analysis and provenance validation.
    """

    evidence = list(evidence_bundle)

    if not evidence:

        return (
            "EVIDENCE CONTEXT\n"
            "Evidence count: 0\n"
            "Useful evidence found: NO\n"
            "No evidence has been retrieved yet."
        )

    source_types = sorted(
        {
            evidence_item.source_type
            for evidence_item in evidence
        }
    )

    tickers = sorted(
        {
            evidence_item.ticker
            for evidence_item in evidence
            if evidence_item.ticker
        }
    )

    citations = sorted(
        {
            evidence_item.citation
            for evidence_item in evidence
            if evidence_item.citation
        }
    )

    header = [
        "EVIDENCE CONTEXT",
        f"Evidence count: {len(evidence)}",
        "Useful evidence found: YES",
        (
            "Source types: "
            + ", ".join(source_types)
        ),
        (
            "Entities/tickers: "
            + (
                ", ".join(tickers)
                if tickers
                else "none"
            )
        ),
        f"Citation count: {len(citations)}",
        "",
        (
            "The full evidence remains available "
            "outside this context. This is a compact "
            "reasoning view."
        ),
        "",
    ]

    selected = evidence[:MAX_EVIDENCE_ITEMS]

    evidence_sections = []

    for index, evidence_item in enumerate(
        selected,
        start=1,
    ):

        evidence_sections.append(
            f"--- Evidence {index} ---\n"
            + _format_single_evidence(
                evidence_item
            )
        )

    if len(evidence) > MAX_EVIDENCE_ITEMS:

        evidence_sections.append(
            "\n--- Evidence truncation notice ---\n"
            f"{len(evidence) - MAX_EVIDENCE_ITEMS} "
            "additional evidence records exist in "
            "the full EvidenceBundle but are not "
            "included in this compact Qwen context.\n"
            "Use an analytical tool or another "
            "retrieval tool if additional detail is required."
        )

    context = "\n".join(
        header + evidence_sections
    )

    if len(context) > MAX_TOTAL_CONTEXT:

        context = (
            context[:MAX_TOTAL_CONTEXT]
            + "\n\n"
            "[Compact context limit reached. "
            "Full EvidenceBundle remains available.]"
        )

    return context