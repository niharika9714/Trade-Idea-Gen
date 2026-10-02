from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data_access.document_parser import (
    parse_document,
    search_document,
    read_document_location,
    document_structure,
)


def get_document_structure(
    source_path: str,
) -> Dict[str, Any]:

    return document_structure(source_path)


def retrieve_document(
    source_path: str,
) -> Dict[str, Any]:

    return parse_document(source_path)


def search_document_evidence(
    source_path: str,
    query: str,
    content_types: Optional[List[str]] = None,
    max_results: int = 10,
) -> Dict[str, Any]:

    return search_document(
        source_path=source_path,
        query=query,
        content_types=content_types,
        max_results=max_results,
    )


def read_document_evidence(
    source_path: str,
    locator: str,
) -> Dict[str, Any]:

    return read_document_location(
        source_path=source_path,
        locator=locator,
    )