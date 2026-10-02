"""
Step 1I - Automated Dataset Integrity & Provenance Validator

Validates the synthetic investment-research dataset before retrieval/tool development.

Run from project root:

    .\.venv\Scripts\python.exe src\data_generation\validate_dataset.py

Exit code:
    0 = PASS
    1 = validation failures
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET

from collections import Counter, defaultdict
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"

DOCUMENT_DIR = DATA_DIR / "documents"

NEWS_JSON_DIR = DATA_DIR / "news" / "source_json"
NEWS_XML_DIR = DATA_DIR / "news" / "stored_xml"

API_DIR = DATA_DIR / "internal_api" / "responses"

MARKET_DB = DATA_DIR / "market_data" / "market.db"

REGISTRY_DB = DATA_DIR / "metadata" / "registry.db"

MANIFEST_FILE = DATA_DIR / "reference" / "document_manifest.json"


# ============================================================
# EXPECTED DATASET CONFIGURATION
# ============================================================

EXPECTED_TICKERS = {
    "D05",
    "O39",
    "U11",
    "HSBA",
    "STAN",
}

EXPECTED_DOC_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".docx",
    ".msg",
}

EXPECTED_TABLES = {
    "daily_prices",
    "daily_volume",
    "fundamentals",
    "sector_prices",
}

REQUIRED_API_PROVENANCE = {
    "source_system",
    "source_type",
    "calculation_type",
    "synthetic",
}


# ============================================================
# VALIDATION STATE
# ============================================================

FAILURES = []
WARNINGS = []


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def sha256(path: Path) -> str:
    """
    Calculate SHA-256 checksum for a file.
    """

    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


def check(name: str, condition: bool, detail: str = ""):
    """
    Record a PASS or FAIL.
    """

    if condition:

        print(
            f"[PASS] {name}"
            + (f" — {detail}" if detail else "")
        )

    else:

        print(
            f"[FAIL] {name}"
            + (f" — {detail}" if detail else "")
        )

        FAILURES.append(
            f"{name}: {detail}"
        )


def warn(name: str, detail: str):
    """
    Record a warning without failing the validation.
    """

    print(
        f"[WARN] {name} — {detail}"
    )

    WARNINGS.append(
        f"{name}: {detail}"
    )


def load_json(path: Path):
    """
    Load JSON file.
    """

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


def ticker_from_name(path: Path):
    """
    Attempt to identify ticker from filename.
    """

    name = path.name.upper()

    for ticker in EXPECTED_TICKERS:

        pattern = (
            rf"(?<![A-Z0-9])"
            rf"{re.escape(ticker)}"
            rf"(?![A-Z0-9])"
        )

        if re.search(pattern, name):

            return ticker

    return None


# ============================================================
# 1. DIRECTORY VALIDATION
# ============================================================

def validate_directories():

    print("\n--- 1. DIRECTORY STRUCTURE ---")

    required_dirs = [

        DATA_DIR,

        DOCUMENT_DIR,

        DOCUMENT_DIR / "pdf",

        DOCUMENT_DIR / "pptx",

        DOCUMENT_DIR / "docx",

        DOCUMENT_DIR / "outlook" / "emails",

        NEWS_JSON_DIR,

        NEWS_XML_DIR,

        DATA_DIR / "market_data",

        API_DIR,

        DATA_DIR / "reference",

        DATA_DIR / "metadata",
    ]

    for directory in required_dirs:

        check(
            f"Directory: {directory.relative_to(ROOT)}",
            directory.is_dir(),
        )


# ============================================================
# 2. DOCUMENT VALIDATION
# ============================================================

def validate_documents():

    print("\n--- 2. DOCUMENT SOURCES ---")

    files = [

        p
        for p in DOCUMENT_DIR.rglob("*")

        if (
            p.is_file()
            and p.suffix.lower()
            in EXPECTED_DOC_EXTENSIONS
        )
    ]

    counts = Counter(
        p.suffix.lower()
        for p in files
    )

    check(
        "Document files discovered",
        len(files) > 0,
        f"{len(files)} files",
    )

    # Check individual formats

    for extension in sorted(
        EXPECTED_DOC_EXTENSIONS
    ):

        count = counts[extension]

        if count == 0:

            warn(
                f"{extension} coverage",
                "No files found",
            )

        else:

            print(
                f"[PASS] {extension} coverage "
                f"— {count} files"
            )

    # Ticker coverage

    ticker_counts = Counter()

    unknown = []

    for path in files:

        ticker = ticker_from_name(path)

        if ticker:

            ticker_counts[ticker] += 1

        elif "sector" not in path.name.lower():

            unknown.append(
                path.name
            )

    for ticker in sorted(
        EXPECTED_TICKERS
    ):

        check(
            f"Document coverage: {ticker}",
            ticker_counts[ticker] > 0,
            f"{ticker_counts[ticker]} files",
        )

    if unknown:

        warn(
            "Ticker detection",
            f"{len(unknown)} document(s) "
            "have no ticker in filename",
        )

    # Outlook MSG validation

    msg_files = [
        p
        for p in files
        if p.suffix.lower() == ".msg"
    ]

    expected_msg_tickers = {
        "D05",
        "O39",
        "U11",
    }

    for ticker in sorted(
        expected_msg_tickers
    ):

        matches = [

            p
            for p in msg_files

            if ticker_from_name(p) == ticker
        ]

        check(
            f"MSG coverage: {ticker}",
            len(matches) > 0,
            f"{len(matches)} MSG file(s)",
        )

    return files


# ============================================================
# 3. NEWS VALIDATION
# ============================================================

def validate_news():

    print("\n--- 3. NEWS SOURCES ---")

    json_files = sorted(
        NEWS_JSON_DIR.glob("*.json")
    )

    xml_files = sorted(
        NEWS_XML_DIR.glob("*.xml")
    )

    check(
        "News JSON files",
        len(json_files) > 0,
        f"{len(json_files)} files",
    )

    check(
        "News XML files",
        len(xml_files) > 0,
        f"{len(xml_files)} files",
    )

    json_ids = set()
    xml_ids = set()

    required_fields = {

        "article_id",

        "ticker",

        "company",

        "sector",

        "publication_datetime",

        "event_datetime",

        "source",

        "headline",

        "summary",

        "body",

        "sentiment",

        "tags",

        "entities",
    }

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    for path in json_files:

        try:

            data = load_json(path)

            # Support different possible structures

            if (
                isinstance(data, dict)
                and "articles" in data
            ):

                articles = data["articles"]

            elif isinstance(data, list):

                articles = data

            else:

                articles = [data]

            for article in articles:

                missing = (
                    required_fields
                    - set(article.keys())
                )

                check(
                    f"News JSON schema: {path.name}",
                    not missing,
                    (
                        f"missing={sorted(missing)}"
                        if missing
                        else "required fields present"
                    ),
                )

                article_id = article.get(
                    "article_id"
                )

                ticker = article.get(
                    "ticker"
                )

                if article_id:

                    json_ids.add(
                        str(article_id)
                    )

                if ticker:

                    check(
                        f"News ticker validity: {path.name}",
                        ticker in EXPECTED_TICKERS,
                        f"ticker={ticker}",
                    )

        except Exception as exc:

            check(
                f"News JSON parse: {path.name}",
                False,
                str(exc),
            )

    # --------------------------------------------------------
    # XML
    # --------------------------------------------------------

    for path in xml_files:

        try:

            root = ET.parse(
                path
            ).getroot()

            articles = root.findall(
                ".//article"
            )

            check(
                f"News XML parse: {path.name}",
                True,
                f"{len(articles)} article node(s)",
            )

            for article in articles:

                metadata = article.find(
                    "metadata"
                )

                if metadata is not None:

                    article_id = (
                        metadata.findtext(
                            "article_id"
                        )
                    )

                    ticker = (
                        metadata.findtext(
                            "ticker"
                        )
                    )

                    if article_id:

                        xml_ids.add(
                            article_id
                        )

                    if ticker:

                        check(
                            f"News XML ticker validity: {path.name}",
                            ticker in EXPECTED_TICKERS,
                            f"ticker={ticker}",
                        )

        except Exception as exc:

            check(
                f"News XML parse: {path.name}",
                False,
                str(exc),
            )

    # --------------------------------------------------------
    # JSON/XML PAIRING
    # --------------------------------------------------------

    if json_ids and xml_ids:

        missing_xml = (
            json_ids - xml_ids
        )

        missing_json = (
            xml_ids - json_ids
        )

        check(
            "News JSON/XML article pairing",
            not missing_xml
            and not missing_json,
            (
                f"missing_xml={sorted(missing_xml)}, "
                f"missing_json={sorted(missing_json)}"
            ),
        )

    print(
        f"[INFO] News articles discovered "
        f"in JSON: {len(json_ids)}"
    )


# ============================================================
# 4. INTERNAL API VALIDATION
# ============================================================

def validate_api():

    print("\n--- 4. INTERNAL API RESPONSES ---")

    files = sorted(
        API_DIR.glob("*.json")
    )

    check(
        "API response files",
        len(files) > 0,
        f"{len(files)} files",
    )

    categories = Counter()

    ticker_files = defaultdict(list)

    for path in files:

        try:

            data = load_json(path)

            ticker = data.get(
                "ticker"
            )

            if ticker:

                ticker_files[
                    ticker
                ].append(
                    path.name
                )

            name = path.stem.lower()

            if (
                "valuation" in name
                and "peer" not in name
            ):

                categories[
                    "valuation"
                ] += 1

            elif "nim" in name:

                categories[
                    "nim_scenario"
                ] += 1

            elif "peer" in name:

                categories[
                    "peer_valuation"
                ] += 1

            # Provenance

            provenance = data.get(
                "provenance",
                {},
            )

            missing = (
                REQUIRED_API_PROVENANCE
                - set(provenance.keys())
            )

            check(
                f"API provenance: {path.name}",
                not missing,
                (
                    f"missing={sorted(missing)}"
                    if missing
                    else "complete"
                ),
            )

            # Synthetic flag

            if "synthetic" in provenance:

                check(
                    f"API synthetic flag: {path.name}",
                    provenance["synthetic"] is True,
                    (
                        f"value="
                        f"{provenance['synthetic']}"
                    ),
                )

        except Exception as exc:

            check(
                f"API JSON parse: {path.name}",
                False,
                str(exc),
            )

    # Ticker coverage

    for ticker in sorted(
        EXPECTED_TICKERS
    ):

        check(
            f"API ticker coverage: {ticker}",
            ticker in ticker_files,
            f"{len(ticker_files[ticker])} response(s)",
        )

    # Category coverage

    for category in (
        "valuation",
        "nim_scenario",
        "peer_valuation",
    ):

        check(
            f"API category: {category}",
            categories[category] > 0,
            f"{categories[category]} file(s)",
        )


# ============================================================
# 5. MARKET DATABASE VALIDATION
# ============================================================

def table_columns(
    conn,
    table,
):

    return {

        row[1]

        for row in conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }


def validate_market_db():

    print("\n--- 5. MARKET DATABASE ---")

    check(
        "Market database exists",
        MARKET_DB.is_file(),
        str(MARKET_DB),
    )

    if not MARKET_DB.is_file():

        return

    try:

        conn = sqlite3.connect(
            MARKET_DB
        )

        tables = {

            row[0]

            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """
            ).fetchall()
        }

        missing_tables = (
            EXPECTED_TABLES - tables
        )

        check(
            "Expected SQL tables",
            not missing_tables,
            (
                f"missing={sorted(missing_tables)}"
                if missing_tables
                else "all present"
            ),
        )

        # Check table population

        for table in sorted(
            EXPECTED_TABLES & tables
        ):

            count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            check(
                f"SQL table populated: {table}",
                count > 0,
                f"{count:,} rows",
            )

        # Check ticker coverage

        for table in (
            "daily_prices",
            "daily_volume",
            "fundamentals",
        ):

            if table not in tables:

                continue

            columns = table_columns(
                conn,
                table,
            )

            if "ticker" not in columns:

                warn(
                    f"SQL ticker coverage: {table}",
                    "No ticker column found",
                )

                continue

            found = {

                row[0]

                for row in conn.execute(
                    f"""
                    SELECT DISTINCT ticker
                    FROM {table}
                    """
                ).fetchall()

                if row[0]
            }

            missing = (
                EXPECTED_TICKERS - found
            )

            check(
                f"SQL ticker coverage: {table}",
                not missing,
                (
                    f"missing={sorted(missing)}"
                    if missing
                    else "all expected tickers present"
                ),
            )

        # daily_prices validation

        if "daily_prices" in tables:

            columns = table_columns(
                conn,
                "daily_prices",
            )

            required = {
                "trade_date",
                "close_price",
            }

            check(
                "daily_prices required columns",
                required <= columns,
                (
                    f"missing="
                    f"{sorted(required - columns)}"
                ),
            )

            if required <= columns:

                nulls = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM daily_prices
                    WHERE trade_date IS NULL
                       OR close_price IS NULL
                    """
                ).fetchone()[0]

                check(
                    "daily_prices null sanity",
                    nulls == 0,
                    f"{nulls} invalid row(s)",
                )

        conn.close()

    except Exception as exc:

        check(
            "Market database readable",
            False,
            str(exc),
        )


# ============================================================
# 6. REGISTRY VALIDATION
# ============================================================

def validate_registry(
    document_files,
):

    print("\n--- 6. REGISTRY & PROVENANCE ---")

    check(
        "Registry database exists",
        REGISTRY_DB.is_file(),
        str(REGISTRY_DB),
    )

    if not REGISTRY_DB.is_file():

        return

    try:

        conn = sqlite3.connect(
            REGISTRY_DB
        )

        tables = {

            row[0]

            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """
            ).fetchall()
        }

        expected = {

            "documents",

            "document_versions",

            "events",

            "document_event_links",

            "ingestion_runs",
        }

        missing = (
            expected - tables
        )

        check(
            "Registry schema",
            not missing,
            (
                f"missing={sorted(missing)}"
                if missing
                else "all expected tables present"
            ),
        )

        if "documents" not in tables:

            conn.close()

            return

        rows = conn.execute(
            """
            SELECT
                document_id,
                source_path,
                status
            FROM documents
            """
        ).fetchall()

        source_paths = [
            row[1]
            for row in rows
        ]

        # ----------------------------------------------------
        # Duplicate paths
        # ----------------------------------------------------

        duplicate_paths = [

            path

            for path, count
            in Counter(
                source_paths
            ).items()

            if count > 1
        ]

        check(
            "Registry duplicate source paths",
            not duplicate_paths,
            (
                f"duplicates="
                f"{duplicate_paths[:5]}"
                if duplicate_paths
                else "none"
            ),
        )

        # ----------------------------------------------------
        # Registered files actually exist
        # ----------------------------------------------------

        missing_sources = []

        for (
            document_id,
            source_path,
            status,
        ) in rows:

            path = ROOT / source_path

            if (
                status not in (
                    "missing",
                    "inactive",
                )
                and not path.is_file()
            ):

                missing_sources.append(
                    (
                        document_id,
                        source_path,
                    )
                )

        check(
            "Registry source-file integrity",
            not missing_sources,
            (
                f"{len(missing_sources)} "
                "missing source file(s)"
            ),
        )

        # ----------------------------------------------------
        # Actual files are registered
        # ----------------------------------------------------

        actual_relative = {

            str(
                p.relative_to(ROOT)
            ).replace(
                "\\",
                "/",
            )

            for p in document_files
        }

        registered_relative = {

            str(path).replace(
                "\\",
                "/",
            )

            for path in source_paths
        }

        unregistered = (
            actual_relative
            - registered_relative
        )

        check(
            "Registry completeness",
            not unregistered,
            (
                f"{len(unregistered)} "
                "discovered file(s) not registered"
            ),
        )

        # ----------------------------------------------------
        # Version records
        # ----------------------------------------------------

        if "document_versions" in tables:

            version_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM document_versions
                """
            ).fetchone()[0]

            check(
                "Registry version records",
                version_count >= len(rows),
                (
                    f"{version_count} version record(s) "
                    f"for {len(rows)} document(s)"
                ),
            )

            # Latest checksum validation

            query = """
                SELECT
                    dv.document_id,
                    dv.source_path,
                    dv.checksum
                FROM document_versions dv
                JOIN (
                    SELECT
                        document_id,
                        MAX(version_number)
                            AS max_version
                    FROM document_versions
                    GROUP BY document_id
                ) latest

                ON dv.document_id =
                    latest.document_id

                AND dv.version_number =
                    latest.max_version
            """

            bad_checksums = []

            for (
                document_id,
                source_path,
                checksum,
            ) in conn.execute(query):

                path = ROOT / source_path

                if (
                    path.is_file()
                    and sha256(path)
                    != checksum
                ):

                    bad_checksums.append(
                        source_path
                    )

            check(
                "Registry checksum integrity",
                not bad_checksums,
                (
                    f"{len(bad_checksums)} "
                    "checksum mismatch(es)"
                ),
            )

        # ----------------------------------------------------
        # Event link validation
        # ----------------------------------------------------

        if (
            "document_event_links"
            in tables
            and "events"
            in tables
        ):

            orphan_links = conn.execute(
                """
                SELECT COUNT(*)
                FROM document_event_links l

                LEFT JOIN documents d
                    ON d.document_id =
                       l.document_id

                LEFT JOIN events e
                    ON e.event_id =
                       l.event_id

                WHERE
                    d.document_id IS NULL
                    OR e.event_id IS NULL
                """
            ).fetchone()[0]

            check(
                "Registry event-link integrity",
                orphan_links == 0,
                f"{orphan_links} orphan link(s)",
            )

        conn.close()

    except Exception as exc:

        check(
            "Registry readable",
            False,
            str(exc),
        )


# ============================================================
# 7. MANIFEST VALIDATION
# ============================================================

def validate_manifest():

    print("\n--- 7. MANIFEST EXPORT ---")

    check(
        "Manifest exists",
        MANIFEST_FILE.is_file(),
        str(MANIFEST_FILE),
    )

    if not MANIFEST_FILE.is_file():

        return

    try:

        data = load_json(
            MANIFEST_FILE
        )

        check(
            "Manifest version",
            "manifest_version" in data,
            f"{data.get('manifest_version')}",
        )

        check(
            "Manifest registry type",
            data.get("registry_type")
            == "incremental_sqlite_registry",
            f"{data.get('registry_type')}",
        )

        check(
            "Manifest documents section",
            isinstance(
                data.get("documents"),
                list,
            ),
            (
                f"{len(data.get('documents', []))}"
                " document(s)"
            ),
        )

    except Exception as exc:

        check(
            "Manifest JSON parse",
            False,
            str(exc),
        )


# ============================================================
# 8. EVENT CONSISTENCY
# ============================================================

def validate_event_consistency():

    print("\n--- 8. EVENT CONSISTENCY ---")

    event_pattern = re.compile(
        r"EVENT[-_](\d+)",
        re.IGNORECASE,
    )

    all_source_files = [

        p

        for base in (
            DOCUMENT_DIR,
            NEWS_JSON_DIR,
            NEWS_XML_DIR,
            API_DIR,
        )

        for p in base.rglob("*")

        if p.is_file()
    ]

    event_counts = Counter()

    for path in all_source_files:

        match = event_pattern.search(
            path.name
        )

        if match:

            event_id = (
                f"EVENT-"
                f"{match.group(1).zfill(3)}"
            )

            event_counts[
                event_id
            ] += 1

    if event_counts:

        print(
            "[INFO] Filename-derived events:"
        )

        for (
            event_id,
            count,
        ) in sorted(
            event_counts.items()
        ):

            print(
                f"       {event_id}: "
                f"{count} source(s)"
            )

    else:

        warn(
            "Event identifiers",
            "No EVENT-### identifiers "
            "found in source filenames",
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 68)

    print(
        "STEP 1I - DATASET INTEGRITY "
        "& PROVENANCE VALIDATOR"
    )

    print("=" * 68)

    print(
        f"Project root: {ROOT}"
    )

    # Run validations

    validate_directories()

    document_files = (
        validate_documents()
    )

    validate_news()

    validate_api()

    validate_market_db()

    validate_registry(
        document_files
    )

    validate_manifest()

    validate_event_consistency()

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print("\n" + "=" * 68)

    print("FINAL RESULT")

    print("=" * 68)

    if FAILURES:

        print(
            f"RESULT: FAIL — "
            f"{len(FAILURES)} failure(s), "
            f"{len(WARNINGS)} warning(s)"
        )

        print("\nFailures:")

        for failure in FAILURES:

            print(
                f"  - {failure}"
            )

        if WARNINGS:

            print("\nWarnings:")

            for warning in WARNINGS:

                print(
                    f"  - {warning}"
                )

        return 1

    print(
        f"RESULT: PASS — "
        f"0 failure(s), "
        f"{len(WARNINGS)} warning(s)"
    )

    if WARNINGS:

        print("\nWarnings:")

        for warning in WARNINGS:

            print(
                f"  - {warning}"
            )

    print(
        "\nDataset is ready for "
        "Step 2 data-access/tool development."
    )

    return 0


if __name__ == "__main__":

    sys.exit(
        main()
    )