from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.data_access.document_parser import (
    parse_document,
)


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".docx",
    ".msg",
}


@dataclass
class ContentSearchMatch:
    source_path: str
    extension: str
    score: float
    matched_terms: list[str]
    evidence: list[dict[str, Any]]


def _tokenize(query: str) -> list[str]:
    """Convert a natural-language query into searchable terms."""

    if not query or not query.strip():
        return []

    tokens = re.findall(
        r"[A-Za-z0-9][A-Za-z0-9_-]*",
        query.lower(),
    )

    stop_words = {
        "what",
        "do",
        "you",
        "know",
        "about",
        "tell",
        "me",
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "of",
        "on",
        "for",
        "and",
        "or",
        "in",
        "to",
        "with",
        "please",
    }

    return list(
        dict.fromkeys(
            token
            for token in tokens
            if token not in stop_words
        )
    )


def _normalise_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, (list, tuple)):
        return " ".join(
            _normalise_text(item)
            for item in value
        )

    if isinstance(value, dict):
        return " ".join(
            _normalise_text(item)
            for item in value.values()
        )

    return str(value)


def _walk_strings(
    value: Any,
    path: str = "",
):
    """
    Recursively walk parsed document output.

    This deliberately does not assume that every parser output
    has exactly the same structure.
    """

    if isinstance(value, str):

        if value.strip():
            yield path, value

        return

    if isinstance(value, dict):

        for key, child in value.items():

            child_path = (
                f"{path}.{key}"
                if path
                else str(key)
            )

            yield from _walk_strings(
                child,
                child_path,
            )

        return

    if isinstance(value, (list, tuple)):

        for index, child in enumerate(value):

            child_path = (
                f"{path}[{index}]"
            )

            yield from _walk_strings(
                child,
                child_path,
            )


def _score_text(
    text: str,
    terms: list[str],
) -> tuple[float, list[str]]:

    if not text or not terms:
        return 0.0, []

    lowered = text.lower()

    matched = []

    for term in terms:

        if term in lowered:
            matched.append(term)

    if not matched:
        return 0.0, []

    score = (
        len(matched)
        / len(terms)
    )

    # Exact phrase match receives an additional boost.
    return score, matched


def search_document_content(
    document_paths: list[str | Path],
    query: str,
    max_results: int = 20,
) -> list[ContentSearchMatch]:

    if not query or not query.strip():
        return []

    if max_results <= 0:
        raise ValueError(
            "max_results must be greater than zero."
        )

    terms = _tokenize(query)

    if not terms:
        return []

    matches = []

    for document_path in document_paths:

        path = Path(document_path)

        if (
            path.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        if not path.exists():
            continue

        try:
            parsed = parse_document(
                str(path)
            )
        except Exception:
            # One corrupt/unsupported document must not
            # prevent the remaining corpus from being searched.
            continue

        document_matches = []

        for location, value in _walk_strings(
            parsed
        ):

            score, matched_terms = _score_text(
                value,
                terms,
            )

            if score <= 0:
                continue

            document_matches.append(
                {
                    "location": location,
                    "text": value,
                    "matched_terms": matched_terms,
                    "score": score,
                }
            )

        if not document_matches:
            continue

        document_matches.sort(
            key=lambda item: (
                item["score"],
                len(item["matched_terms"]),
            ),
            reverse=True,
        )

        document_score = max(
            item["score"]
            for item in document_matches
        )

        matches.append(
            ContentSearchMatch(
                source_path=str(path),
                extension=path.suffix.lower(),
                score=document_score,
                matched_terms=list(
                    dict.fromkeys(
                        term
                        for item in document_matches
                        for term in item[
                            "matched_terms"
                        ]
                    )
                ),
                evidence=document_matches,
            )
        )

    matches.sort(
        key=lambda item: (
            item.score,
            len(item.matched_terms),
        ),
        reverse=True,
    )

    return matches[:max_results]