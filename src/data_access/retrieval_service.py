"""
Step 2D - Unified Retrieval Service

Provides one controlled retrieval interface across:
    - SQL market data
    - Documents
    - News
    - Internal APIs

All retrieval results are normalized into EvidenceBundle objects.

This layer does NOT:
    - use embeddings
    - use a vector database
    - call an LLM
    - perform investment reasoning
    - fabricate citations

It is purely a retrieval/orchestration layer.

Design principles:
    1. Deterministic retrieval.
    2. Source-native retrieval.
    3. First-class provenance.
    4. Evidence-level deduplication.
    5. Explicit input validation.
    6. Empty results are valid results.
    7. Retrieval failures are surfaced as warnings.
"""

from pathlib import Path
import json
import re
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data access imports
# ---------------------------------------------------------------------------

from src.data_access.file_access import (
    search_files,
    get_file_metadata,
)

from src.data_access.sql_access import (
    get_price_history,
    get_fundamentals,
    get_volume_history,
    execute_query,
)

from src.data_access.api_access import (
    find_api_responses,
    get_api_response,
)

from src.data_access.document_parser import (
    parse_document,
)

from src.data_access.content_search import (
    search_document_content,
)

# ---------------------------------------------------------------------------
# Provenance imports
# ---------------------------------------------------------------------------

from src.provenance.document_evidence import (
    document_to_evidence,
    search_document_to_evidence,
)

from src.provenance.sql_evidence import (
    sql_rows_to_evidence,
)

from src.provenance.api_evidence import (
    api_response_to_evidence,
)

from src.provenance.news_evidence import (
    news_articles_to_evidence,
)

from src.provenance.evidence import (
    EvidenceBundle,
)


# ===========================================================================
# PATHS
# ===========================================================================

ROOT = Path(__file__).resolve().parents[2]

NEWS_SOURCE_DIR = (
    ROOT
    / "data"
    / "news"
    / "source_json"
)


# ===========================================================================
# CONSTANTS
# ===========================================================================

SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".docx",
    ".msg",
}

DEFAULT_DOCUMENT_LIMIT = 20
DEFAULT_NEWS_LIMIT = 20
DEFAULT_SQL_LIMIT = 500

MAX_DOCUMENT_LIMIT = 100
MAX_NEWS_LIMIT = 100
MAX_SQL_LIMIT = 5000


# ===========================================================================
# INTERNAL HELPERS
# ===========================================================================

def _empty_bundle() -> EvidenceBundle:
    """
    Return a new empty EvidenceBundle.
    """

    return EvidenceBundle()


def _normalize_ticker(
    ticker: Optional[str],
) -> Optional[str]:
    """
    Normalize ticker input.

    Examples:
        D05   -> D05
        d05   -> D05
        " D05 " -> D05
        None  -> None
    """

    if ticker is None:
        return None

    ticker = str(ticker).strip().upper()

    if not ticker:
        return None

    return ticker


def _validate_limit(
    limit: int,
    maximum: int,
    field_name: str = "limit",
) -> int:
    """
    Validate retrieval limits.
    """

    if not isinstance(limit, int):
        raise TypeError(
            f"{field_name} must be an integer."
        )

    if limit <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    if limit > maximum:
        raise ValueError(
            f"{field_name} cannot exceed {maximum}."
        )

    return limit


def _normalize_extension(
    extension: Optional[str],
) -> Optional[str]:
    """
    Normalize a document extension.

    Examples:
        pdf  -> .pdf
        .PDF -> .pdf
    """

    if extension is None:
        return None

    normalized = str(extension).strip().lower()

    if not normalized:
        return None

    if not normalized.startswith("."):
        normalized = "." + normalized

    return normalized


def _validate_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
) -> None:
    """
    Validate ISO-style date range.

    The project currently uses YYYY-MM-DD strings.
    """

    if start_date and end_date:

        if str(start_date) > str(end_date):

            raise ValueError(
                "start_date cannot be later than end_date."
            )


def _tokenize_text(
    value: Any,
) -> set[str]:
    """
    Convert text into normalized lexical tokens.

    This is deliberately deterministic.

    No:
        - embeddings
        - semantic search
        - LLM
    """

    return set(
        re.findall(
            r"\b[a-z0-9]+(?:\.[a-z0-9]+)?\b",
            str(value).lower(),
        )
    )


def _add_evidence(
    bundle: EvidenceBundle,
    evidence: Any,
    existing_ids: Optional[set[str]] = None,
) -> None:
    """
    Add evidence while preventing duplicate Evidence IDs.

    EvidenceBundle.add() may already provide deduplication,
    but this helper makes the retrieval-service contract explicit.
    """

    if existing_ids is None:
        existing_ids = set(bundle.ids())

    evidence_id = getattr(
        evidence,
        "evidence_id",
        None,
    )

    if evidence_id is None:
        bundle.add(evidence)
        return

    if evidence_id in existing_ids:
        return

    bundle.add(evidence)
    existing_ids.add(evidence_id)


# ===========================================================================
# NEWS LOADING
# ===========================================================================

def _load_news_articles() -> list[dict[str, Any]]:
    """
    Load all synthetic news JSON files.

    The news generator stores raw articles under:

        data/news/source_json/

    Returns:
        List of article dictionaries.

    Notes:
        Malformed files are skipped rather than causing complete
        retrieval failure. The current Step 2D contract does not
        yet expose retrieval warnings as a structured result.
    """

    articles: list[dict[str, Any]] = []

    if not NEWS_SOURCE_DIR.exists():
        return articles

    for path in sorted(
        NEWS_SOURCE_DIR.glob("*.json")
    ):

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as handle:

                payload = json.load(handle)

            if isinstance(payload, list):

                articles.extend(payload)

            elif isinstance(payload, dict):

                if isinstance(
                    payload.get("articles"),
                    list,
                ):

                    articles.extend(
                        payload["articles"]
                    )

                else:

                    articles.append(payload)

        except (
            OSError,
            json.JSONDecodeError,
        ):

            # Do not let one malformed source
            # destroy the entire retrieval request.
            continue

    return articles


# ===========================================================================
# NEWS MATCHING
# ===========================================================================

def _matches_text(
    article: dict[str, Any],
    query: str,
) -> bool:
    """
    Deterministic lexical matching for news.

    Matching strategy:

        1. Empty query -> match everything.
        2. Exact phrase match.
        3. Otherwise require every query token
           to exist in the article text.

    Example:

        query = "D05 earnings"

    Matches:

        "D05 reported strong quarterly results.
         Earnings improved..."

    even though "D05" and "earnings" are not adjacent.

    This is lexical AND matching, not semantic retrieval.
    """

    query = (
        query or ""
    ).lower().strip()

    if not query:
        return True

    searchable_fields = [
        article.get("headline", ""),
        article.get("summary", ""),
        article.get("body", ""),
        article.get("ticker", ""),
        article.get("company", ""),
        article.get("sector", ""),
        article.get("event_id", ""),
    ]

    searchable_text = " ".join(
        str(value)
        for value in searchable_fields
        if value is not None
    ).lower()

    # ---------------------------------------------------------------
    # Exact phrase match
    # ---------------------------------------------------------------

    if query in searchable_text:
        return True

    # ---------------------------------------------------------------
    # Token-level AND matching
    # ---------------------------------------------------------------

    searchable_tokens = _tokenize_text(
        searchable_text
    )

    query_tokens = _tokenize_text(
        query
    )

    if not query_tokens:
        return True

    return query_tokens.issubset(
        searchable_tokens
    )


# ===========================================================================
# DOCUMENT RETRIEVAL
# ===========================================================================
def search_documents(
    query: str,
    ticker: Optional[str] = None,
    event_id: Optional[str] = None,
    extension: Optional[str] = None,
    max_results: int = DEFAULT_DOCUMENT_LIMIT,
) -> EvidenceBundle:
    """
    Search supported documents by their actual content.

    Filename/path matching is used only to discover candidate documents.
    The user's query is then matched against parsed document content.

    Supported:
        - PDF
        - PPTX
        - DOCX
        - MSG

    No embeddings, vector database, GraphRAG, or LLM retrieval is used.
    """

    max_results = _validate_limit(
        max_results,
        MAX_DOCUMENT_LIMIT,
        "max_results",
    )

    ticker = _normalize_ticker(ticker)

    normalized_extension = _normalize_extension(
        extension
    )

    if normalized_extension:

        if (
            normalized_extension
            not in SUPPORTED_DOCUMENT_EXTENSIONS
        ):
            raise ValueError(
                "Unsupported document extension: "
                f"{normalized_extension}"
            )

        extensions_to_search = [
            normalized_extension
        ]

    else:

        extensions_to_search = sorted(
            SUPPORTED_DOCUMENT_EXTENSIONS
        )

    query = (
        query or ""
    ).strip()

    if not query:
        return _empty_bundle()

    # ------------------------------------------------------------------
    # 1. Discover candidate document paths.
    #
    # IMPORTANT:
    # Do not use the user's query for filename discovery.
    # We want content-based retrieval.
    # ------------------------------------------------------------------

    candidates_by_path: dict[
        str,
        dict[str, Any],
    ] = {}

    for current_extension in extensions_to_search:

        candidates = search_files(
            query="",
            ticker=ticker,
            event_id=event_id,
            extension=current_extension,
            max_results=MAX_DOCUMENT_LIMIT,
        )

        for candidate in candidates:

            source_path = candidate.get(
                "source_path"
            )

            if not source_path:
                continue

            candidate_extension = (
                Path(source_path)
                .suffix
                .lower()
            )

            if (
                candidate_extension
                not in SUPPORTED_DOCUMENT_EXTENSIONS
            ):
                continue

            candidates_by_path[
                source_path
            ] = candidate

    document_paths = sorted(
        candidates_by_path.keys()
    )

    if not document_paths:
        return _empty_bundle()

    # ------------------------------------------------------------------
    # 2. Search actual document content.
    # ------------------------------------------------------------------

    matches = search_document_content(
        document_paths=document_paths,
        query=query,
        max_results=max_results,
    )

    bundle = _empty_bundle()

    existing_ids = set(
        bundle.ids()
    )

    # ------------------------------------------------------------------
    # 3. Convert content-search locations into real Evidence.
    #
    # content_search returns locations such as:
    #
    #     evidence[4].text
    #
    # document_to_evidence() returns an EvidenceBundle.
    #
    # Therefore we convert the bundle to a list before using indexes.
    # ------------------------------------------------------------------

    for match in matches:

        source_path = match.source_path

        if not source_path:
            continue

        matched_indexes: set[int] = set()

        for item in match.evidence:

            location = (
                item.get("location", "")
                or ""
            )

            match_index = re.match(
                r"^evidence\[(\d+)\]\.",
                location,
            )

            if match_index:

                matched_indexes.add(
                    int(
                        match_index.group(1)
                    )
                )

        if not matched_indexes:
            continue

        try:

            document_bundle = (
                document_to_evidence(
                    source_path
                )
            )

            document_items = list(
                document_bundle
            )

            for evidence_index in sorted(
                matched_indexes
            ):

                if (
                    evidence_index < 0
                    or evidence_index >= len(
                        document_items
                    )
                ):
                    continue

                evidence = document_items[
                    evidence_index
                ]

                _add_evidence(
                    bundle,
                    evidence,
                    existing_ids,
                )

        except Exception as exc:

            print(
                "[WARN] Could not convert content-search "
                f"match into Evidence for "
                f"{source_path}: {exc}"
            )

    return bundle

# ===========================================================================
# DOCUMENT RETRIEVAL - COMPLETE DOCUMENT
# ===========================================================================

def get_document(
    source_path: str,
) -> EvidenceBundle:
    """
    Retrieve an entire document as unified Evidence.

    Args:
        source_path:
            Absolute or project-relative source path.

    Returns:
        EvidenceBundle
    """

    if not source_path:
        raise ValueError(
            "source_path is required."
        )

    return document_to_evidence(
        source_path
    )


# ===========================================================================
# DOCUMENT STRUCTURE
# ===========================================================================

def get_document_structure(
    source_path: str,
) -> dict[str, Any]:
    """
    Return the structural representation of a document.

    This intentionally does NOT convert the structure into Evidence.

    It is metadata describing how a document can be navigated.
    """

    if not source_path:
        raise ValueError(
            "source_path is required."
        )

    parsed = parse_document(
        source_path
    )

    return {
        "source_path": source_path,
        "document_type": parsed.get(
            "document_type"
        ),
        "structure": parsed,
    }


# ===========================================================================
# SQL - PRICE DATA
# ===========================================================================

def get_prices(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = DEFAULT_SQL_LIMIT,
    latest: bool = False,
) -> EvidenceBundle:
    """
    Retrieve historical market prices.
    """

    ticker = _normalize_ticker(
        ticker
    )

    if not ticker:
        raise ValueError(
            "Ticker is required for get_prices."
        )

    limit = _validate_limit(
        limit,
        MAX_SQL_LIMIT,
    )

    _validate_date_range(
        start_date,
        end_date,
    )
    if latest:
        limit = 1

    result = get_price_history(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        latest=latest,
    )

    return sql_rows_to_evidence(
        rows=result["rows"],
        table_name="daily_prices",
        query=result["query"],
        ticker=ticker,
        locator_field="trade_date",
    )


# ===========================================================================
# SQL - FUNDAMENTALS
# ===========================================================================

def get_fundamental_data(
    ticker: str,
    limit: int = 20,
) -> EvidenceBundle:
    """
    Retrieve fundamental data.
    """

    ticker = _normalize_ticker(
        ticker
    )

    if not ticker:
        raise ValueError(
            "Ticker is required for "
            "get_fundamental_data."
        )

    limit = _validate_limit(
        limit,
        MAX_SQL_LIMIT,
    )

    rows = get_fundamentals(
        ticker=ticker,
        limit=limit,
    )

    return sql_rows_to_evidence(
        rows=rows,
        table_name="fundamentals",
        query=(
            "get_fundamentals("
            f"ticker={ticker}, "
            f"limit={limit})"
        ),
        ticker=ticker,
        locator_field="report_date",
    )


# ===========================================================================
# SQL - VOLUME
# ===========================================================================

def get_volume(
    ticker: str,
    limit: int = 100,
) -> EvidenceBundle:
    """
    Retrieve historical trading volume.
    """

    ticker = _normalize_ticker(
        ticker
    )

    if not ticker:
        raise ValueError(
            "Ticker is required for get_volume."
        )

    limit = _validate_limit(
        limit,
        MAX_SQL_LIMIT,
    )

    result = get_volume_history(
        ticker=ticker,
        limit=limit,
    )

    return sql_rows_to_evidence(
        rows=result["rows"],
        table_name="daily_volume",
        query=result["query"],
        ticker=ticker,
        locator_field="trade_date",
    )


# ===========================================================================
# SQL - GENERIC ANALYTICAL QUERY
# ===========================================================================

def run_sql(
    sql: str,
    parameters: tuple = (),
    ticker: Optional[str] = None,
    table_name: str = "query_result",
    locator_field: Optional[str] = None,
    max_rows: int = DEFAULT_SQL_LIMIT,
) -> EvidenceBundle:
    """
    Execute a controlled SELECT/WITH query and convert rows
    directly into Evidence.

    This is the future foundation for agent-driven analytical
    queries such as:

        SELECT AVG(close_price)
        FROM daily_prices
        WHERE ticker = ?

    The underlying execute_query() already restricts execution
    to read-only SELECT/WITH statements.

    Important:
        table_name is currently a provenance label supplied by
        the caller. The actual SQL query remains the authoritative
        database operation.
    """

    if not isinstance(
        sql,
        str,
    ):
        raise TypeError(
            "sql must be a string."
        )

    sql = sql.strip()

    if not sql:
        raise ValueError(
            "sql is required."
        )

    max_rows = _validate_limit(
        max_rows,
        MAX_SQL_LIMIT,
        "max_rows",
    )

    ticker = _normalize_ticker(
        ticker
    )

    result = execute_query(
        sql=sql,
        parameters=parameters,
        max_rows=max_rows,
    )

    return sql_rows_to_evidence(
        rows=result["rows"],
        table_name=table_name,
        query=sql,
        ticker=ticker,
        locator_field=locator_field,
    )



# ===========================================================================
# INTERNAL API RETRIEVAL
# ===========================================================================

def get_internal_api(
    ticker: Optional[str] = None,
    response_type: Optional[str] = None,
) -> EvidenceBundle:
    """
    Retrieve synthetic internal API responses.
    """

    ticker = _normalize_ticker(
        ticker
    )

    responses = find_api_responses(
        ticker=ticker,
        response_type=response_type,
    )

    bundle = _empty_bundle()

    existing_ids = set(
        bundle.ids()
    )

    for response_info in responses:

        filename = response_info.get(
            "filename"
        )

        if not filename:
            continue

        try:

            response = get_api_response(
                filename
            )

            response_bundle = (
                api_response_to_evidence(
                    response=response,
                    filename=filename,
                    ticker=ticker,
                )
            )

            for evidence in response_bundle:

                _add_evidence(
                    bundle,
                    evidence,
                    existing_ids,
                )

        except Exception as exc:

            print(
                "[WARN] Could not retrieve API "
                f"response {filename}: {exc}"
            )

    return bundle


# ===========================================================================
# NEWS RETRIEVAL
# ===========================================================================

def search_news(
    query: str = "",
    ticker: Optional[str] = None,
    event_id: Optional[str] = None,
    limit: int = DEFAULT_NEWS_LIMIT,
) -> EvidenceBundle:
    """
    Search synthetic financial news.

    Matching is deterministic lexical filtering.

    Matching supports:

        - exact phrase
        - multi-term lexical AND matching

    Args:
        query:
            Text to search in:
                headline
                summary
                body
                company
                ticker
                sector
                event ID

        ticker:
            Optional ticker restriction.

        event_id:
            Optional event restriction.

        limit:
            Maximum articles returned.
    """

    ticker = _normalize_ticker(
        ticker
    )

    limit = _validate_limit(
        limit,
        MAX_NEWS_LIMIT,
    )

    query = (
        query or ""
    ).strip()

    articles = _load_news_articles()

    matched: list[
        dict[str, Any]
    ] = []

    for article in articles:

        # -----------------------------------------------------------
        # Ticker restriction
        # -----------------------------------------------------------

        if ticker:

            article_ticker = (
                article.get(
                    "ticker",
                    "",
                )
                or ""
            ).upper()

            if article_ticker != ticker:
                continue

        # -----------------------------------------------------------
        # Event restriction
        # -----------------------------------------------------------

        if event_id:

            if (
                article.get("event_id")
                != event_id
            ):
                continue

        # -----------------------------------------------------------
        # Text matching
        # -----------------------------------------------------------

        if not _matches_text(
            article,
            query,
        ):
            continue

        matched.append(
            article
        )

    # ---------------------------------------------------------------
    # Most recent first
    # ---------------------------------------------------------------

    matched.sort(
        key=lambda article: article.get(
            "publication_datetime",
            "",
        ),
        reverse=True,
    )

    matched = matched[
        :limit
    ]

    return news_articles_to_evidence(
        matched
    )


# ===========================================================================
# SOURCE DISCOVERY
# ===========================================================================

def discover_sources(
    query: str,
    ticker: Optional[str] = None,
    event_id: Optional[str] = None,
    extension: Optional[str] = None,
    max_results: int = DEFAULT_DOCUMENT_LIMIT,
) -> list[dict[str, Any]]:
    """
    Discover candidate source files without reading their contents.

    This returns source metadata rather than EvidenceBundle because
    the purpose of this operation is source discovery.

    The caller can subsequently use get_document() or
    search_documents() to retrieve actual evidence.
    """

    max_results = _validate_limit(
        max_results,
        MAX_DOCUMENT_LIMIT,
        "max_results",
    )

    ticker = _normalize_ticker(
        ticker
    )

    normalized_extension = _normalize_extension(
        extension
    )

    return search_files(
        query=(query or "").strip(),
        ticker=ticker,
        event_id=event_id,
        extension=normalized_extension,
        max_results=max_results,
    )


# ===========================================================================
# SOURCE METADATA
# ===========================================================================

def source_metadata(
    source_path: str,
) -> dict[str, Any]:
    """
    Return metadata for a source file.
    """

    if not source_path:
        raise ValueError(
            "source_path is required."
        )

    return get_file_metadata(
        source_path
    )
