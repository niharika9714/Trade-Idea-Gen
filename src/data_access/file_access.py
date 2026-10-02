"""
Native file retrieval tools.

Purpose:
    Search and retrieve original source files without embeddings
    or a vector database.

Supported:
    PDF
    PPTX
    DOCX
    MSG
    JSON
    XML

Important:
    These tools return provenance together with retrieved content.
"""

from __future__ import annotations

import hashlib
import json
import re

from pathlib import Path
from typing import Any, Optional


# ============================================================
# PROJECT PATH
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"

DOCUMENT_DIR = DATA_DIR / "documents"

NEWS_DIR = DATA_DIR / "news"

API_DIR = DATA_DIR / "internal_api" / "responses"


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".docx",
    ".msg",
    ".json",
    ".xml",
}


# ============================================================
# UTILITY
# ============================================================

def calculate_sha256(path: Path) -> str:

    sha = hashlib.sha256()

    with path.open("rb") as file:

        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):

            sha.update(block)

    return sha.hexdigest()


def relative_path(path: Path) -> str:

    return str(
        path.relative_to(ROOT)
    ).replace("\\", "/")


def detect_ticker(
    filename: str,
) -> Optional[str]:

    tickers = {
        "D05",
        "O39",
        "U11",
        "HSBA",
        "STAN",
    }

    name = filename.upper()

    for ticker in tickers:

        pattern = (
            rf"(?<![A-Z0-9])"
            rf"{re.escape(ticker)}"
            rf"(?![A-Z0-9])"
        )

        if re.search(pattern, name):

            return ticker

    return None


def detect_event(
    filename: str,
) -> Optional[str]:

    match = re.search(
        r"EVENT[-_](\d+)",
        filename,
        re.IGNORECASE,
    )

    if not match:

        return None

    return (
        f"EVENT-"
        f"{match.group(1).zfill(3)}"
    )


# ============================================================
# FILE SEARCH
# ============================================================

def search_files(
    query: str,
    ticker: Optional[str] = None,
    event_id: Optional[str] = None,
    extension: Optional[str] = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """
    Search source files using deterministic metadata and
    filename/path matching.

    This is NOT semantic/vector search.

    Example:

        search_files(
            query="interest margin",
            ticker="D05"
        )
    """

    query_terms = [
        term.lower()
        for term in re.findall(
            r"\b\w+\b",
            query,
        )
    ]

    candidates = []

    search_roots = [
        DOCUMENT_DIR,
        NEWS_DIR,
        API_DIR,
    ]

    for root in search_roots:

        if not root.exists():

            continue

        for path in root.rglob("*"):

            if not path.is_file():

                continue

            if (
                path.suffix.lower()
                not in SUPPORTED_EXTENSIONS
            ):

                continue

            # Extension filter

            if extension:

                normalized = extension.lower()

                if not normalized.startswith("."):

                    normalized = "." + normalized

                if path.suffix.lower() != normalized:

                    continue

            detected_ticker = detect_ticker(
                path.name
            )

            detected_event = detect_event(
                path.name
            )

            # Metadata filters

            if (
                ticker
                and detected_ticker != ticker
            ):

                continue

            if (
                event_id
                and detected_event != event_id
            ):

                continue

            searchable_text = (
                path.name.lower()
                + " "
                + relative_path(path).lower()
            )

            score = 0

            for term in query_terms:

                if term in searchable_text:

                    score += 1

            # If no query was supplied, accept all files.

            if not query_terms:

                score = 1

            if score == 0:

                continue

            candidates.append(
                {
                    "source_path": relative_path(path),

                    "filename": path.name,

                    "extension": path.suffix.lower(),

                    "ticker": detected_ticker,

                    "event_id": detected_event,

                    "size_bytes": path.stat().st_size,

                    "modified_time": (
                        path.stat().st_mtime
                    ),

                    "match_score": score,

                    "checksum": calculate_sha256(path),

                    "source_type": (
                        path.suffix.lower()
                        .replace(".", "")
                    ),

                }
            )

    candidates.sort(
        key=lambda x: (
            -x["match_score"],
            x["source_path"],
        )
    )

    return candidates[:max_results]


# ============================================================
# READ JSON
# ============================================================

def read_json(
    source_path: str,
) -> dict[str, Any]:

    path = ROOT / source_path

    if not path.is_file():

        raise FileNotFoundError(
            f"Source not found: {source_path}"
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return {
        "content_type": "json",

        "source": {
            "source_path": relative_path(path),

            "filename": path.name,

            "checksum": calculate_sha256(path),

            "source_type": "json",
        },

        "content": data,

        "provenance": {
            "retrieval_method": "direct_file_read",

            "source_system": "synthetic_dataset",

            "synthetic": True,
        },
    }


# ============================================================
# READ XML
# ============================================================

def read_xml(
    source_path: str,
) -> dict[str, Any]:

    path = ROOT / source_path

    if not path.is_file():

        raise FileNotFoundError(
            f"Source not found: {source_path}"
        )

    xml_text = path.read_text(
        encoding="utf-8"
    )

    return {
        "content_type": "xml",

        "source": {
            "source_path": relative_path(path),

            "filename": path.name,

            "checksum": calculate_sha256(path),

            "source_type": "xml",
        },

        "content": xml_text,

        "provenance": {
            "retrieval_method": "direct_file_read",

            "source_system": "synthetic_news_store",

            "synthetic": True,
        },
    }


# ============================================================
# READ RAW FILE
# ============================================================

def read_raw_file(
    source_path: str,
) -> dict[str, Any]:

    path = ROOT / source_path

    if not path.is_file():

        raise FileNotFoundError(
            f"Source not found: {source_path}"
        )

    extension = path.suffix.lower()

    if extension == ".json":

        return read_json(
            source_path
        )

    if extension == ".xml":

        return read_xml(
            source_path
        )

    # For binary/document files we initially return
    # source metadata and raw bytes.

    data = path.read_bytes()

    return {
        "content_type": extension,

        "source": {
            "source_path": relative_path(path),

            "filename": path.name,

            "checksum": calculate_sha256(path),

            "source_type": (
                extension.replace(".", "")
            ),

            "size_bytes": len(data),
        },

        "content": data,

        "provenance": {
            "retrieval_method": "direct_file_read",

            "source_system": "synthetic_dataset",

            "synthetic": True,
        },
    }


# ============================================================
# READ DOCUMENT METADATA
# ============================================================

def get_file_metadata(
    source_path: str,
) -> dict[str, Any]:

    path = ROOT / source_path

    if not path.is_file():

        raise FileNotFoundError(
            f"Source not found: {source_path}"
        )

    return {
        "source_path": relative_path(path),

        "filename": path.name,

        "extension": path.suffix.lower(),

        "size_bytes": path.stat().st_size,

        "checksum": calculate_sha256(path),

        "ticker": detect_ticker(
            path.name
        ),

        "event_id": detect_event(
            path.name
        ),

        "source_type": (
            path.suffix.lower()
            .replace(".", "")
        ),
    }