from pathlib import Path
import sqlite3
import hashlib
import json
import re
from datetime import datetime


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"

DOCUMENT_DIR = DATA_DIR / "documents"
NEWS_DIR = DATA_DIR / "news"
API_DIR = DATA_DIR / "internal_api" / "responses"

METADATA_DIR = DATA_DIR / "metadata"

REGISTRY_DB = METADATA_DIR / "registry.db"

MANIFEST_DIR = DATA_DIR / "reference"
MANIFEST_FILE = MANIFEST_DIR / "document_manifest.json"


# ============================================================
# COMPANY MASTER
# ============================================================

COMPANIES = {
    "D05": {
        "company": "DBS Group",
        "sector": "Singapore Banks"
    },
    "O39": {
        "company": "OCBC",
        "sector": "Singapore Banks"
    },
    "U11": {
        "company": "UOB",
        "sector": "Singapore Banks"
    },
    "HSBA": {
        "company": "HSBC",
        "sector": "Global Banks"
    },
    "STAN": {
        "company": "Standard Chartered",
        "sector": "Global Banks"
    }
}


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database(connection):

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            source_path TEXT NOT NULL UNIQUE,
            filename TEXT NOT NULL,
            source_type TEXT NOT NULL,
            ticker TEXT,
            company TEXT,
            sector TEXT,
            document_type TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            current_version INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_versions (
            document_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            file_size_bytes INTEGER,
            checksum_sha256 TEXT NOT NULL,
            discovered_at TEXT NOT NULL,
            UNIQUE(document_id, version_number),
            FOREIGN KEY(document_id)
                REFERENCES documents(document_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            ticker TEXT,
            company TEXT,
            sector TEXT,
            event_type TEXT,
            event_date TEXT,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_event_links (
            document_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 1.0,
            created_at TEXT NOT NULL,

            PRIMARY KEY(document_id, event_id),

            FOREIGN KEY(document_id)
                REFERENCES documents(document_id),

            FOREIGN KEY(event_id)
                REFERENCES events(event_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_runs (
            ingestion_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            discovered_count INTEGER DEFAULT 0,
            new_count INTEGER DEFAULT 0,
            updated_count INTEGER DEFAULT 0,
            unchanged_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0
        )
    """)

    connection.commit()


# ============================================================
# FILE HASH
# ============================================================

def calculate_sha256(path):

    sha256 = hashlib.sha256()

    with open(path, "rb") as file:

        while True:

            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# TICKER DETECTION
# ============================================================

def detect_ticker(filename):

    filename_upper = filename.upper()

    for ticker in COMPANIES:

        if ticker in filename_upper:
            return ticker

    return None


# ============================================================
# DOCUMENT TYPE
# ============================================================

def detect_document_type(path):

    name = path.name.lower()

    if path.suffix.lower() == ".msg":
        return "email"

    if path.suffix.lower() == ".pdf":

        if "earnings" in name:
            return "earnings_report"

        if "research" in name:
            return "research_report"

        return "pdf_document"

    if path.suffix.lower() == ".pptx":
        return "analyst_deck"

    if path.suffix.lower() == ".docx":
        return "research_note"

    if path.suffix.lower() == ".json":

        if "valuation" in name:
            return "valuation_response"

        if "nim" in name:
            return "scenario_response"

        if "peer" in name:
            return "peer_valuation_response"

        return "api_response"

    if path.suffix.lower() == ".xml":
        return "news_article"

    return "unknown"


# ============================================================
# SOURCE TYPE
# ============================================================

def detect_source_type(path):

    extension = path.suffix.lower()

    mapping = {
        ".pdf": "pdf",
        ".pptx": "pptx",
        ".docx": "docx",
        ".msg": "outlook_email",
        ".json": "json",
        ".xml": "xml"
    }

    return mapping.get(extension, "unknown")


# ============================================================
# EVENT DETECTION
# ============================================================

def detect_event(path, ticker):

    if not ticker:
        return None

    filename = path.name.upper()

    match = re.search(
        r"EVENT[-_]?(\d+)",
        filename
    )

    if match:

        number = match.group(1)

        return f"{ticker}-EVENT-{number.zfill(3)}"

    return None


# ============================================================
# DOCUMENT ID
# ============================================================

def generate_document_id(path):

    relative = path.relative_to(ROOT).as_posix()

    digest = hashlib.sha1(
        relative.encode("utf-8")
    ).hexdigest()[:12]

    return f"DOC-{digest.upper()}"


# ============================================================
# DISCOVER FILES
# ============================================================

def discover_files():

    discovered = []

    search_roots = [
        DOCUMENT_DIR,
        NEWS_DIR,
        API_DIR
    ]

    allowed_extensions = {
        ".pdf",
        ".pptx",
        ".docx",
        ".msg",
        ".json",
        ".xml"
    }

    for root in search_roots:

        if not root.exists():
            continue

        for path in root.rglob("*"):

            if not path.is_file():
                continue

            if path.suffix.lower() not in allowed_extensions:
                continue

            # Ignore the manifest itself
            if path == MANIFEST_FILE:
                continue

            discovered.append(path)

    return discovered


# ============================================================
# REGISTER DOCUMENT
# ============================================================

def register_document(
    connection,
    path,
    ingestion_time
):

    cursor = connection.cursor()

    source_path = path.relative_to(ROOT).as_posix()

    filename = path.name

    document_id = generate_document_id(path)

    ticker = detect_ticker(filename)

    company = None
    sector = None

    if ticker in COMPANIES:

        company = COMPANIES[ticker]["company"]
        sector = COMPANIES[ticker]["sector"]

    source_type = detect_source_type(path)

    document_type = detect_document_type(path)

    checksum = calculate_sha256(path)

    file_size = path.stat().st_size

    existing = cursor.execute(
        """
        SELECT
            document_id,
            current_version
        FROM documents
        WHERE source_path = ?
        """,
        (source_path,)
    ).fetchone()

    # --------------------------------------------------------
    # NEW DOCUMENT
    # --------------------------------------------------------

    if existing is None:

        cursor.execute(
            """
            INSERT INTO documents (
                document_id,
                source_path,
                filename,
                source_type,
                ticker,
                company,
                sector,
                document_type,
                first_seen_at,
                last_seen_at,
                current_version,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                source_path,
                filename,
                source_type,
                ticker,
                company,
                sector,
                document_type,
                ingestion_time,
                ingestion_time,
                1,
                "active"
            )
        )

        cursor.execute(
            """
            INSERT INTO document_versions (
                document_id,
                version_number,
                file_size_bytes,
                checksum_sha256,
                discovered_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                document_id,
                1,
                file_size,
                checksum,
                ingestion_time
            )
        )

        return "new", document_id, ticker

    # --------------------------------------------------------
    # EXISTING DOCUMENT
    # --------------------------------------------------------

    document_id = existing[0]
    current_version = existing[1]

    latest_version = cursor.execute(
        """
        SELECT checksum_sha256
        FROM document_versions
        WHERE document_id = ?
        ORDER BY version_number DESC
        LIMIT 1
        """,
        (document_id,)
    ).fetchone()

    latest_checksum = latest_version[0]

    # --------------------------------------------------------
    # UNCHANGED
    # --------------------------------------------------------

    if latest_checksum == checksum:

        cursor.execute(
            """
            UPDATE documents
            SET last_seen_at = ?
            WHERE document_id = ?
            """,
            (
                ingestion_time,
                document_id
            )
        )

        return "unchanged", document_id, ticker

    # --------------------------------------------------------
    # UPDATED VERSION
    # --------------------------------------------------------

    new_version = current_version + 1

    cursor.execute(
        """
        INSERT INTO document_versions (
            document_id,
            version_number,
            file_size_bytes,
            checksum_sha256,
            discovered_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            document_id,
            new_version,
            file_size,
            checksum,
            ingestion_time
        )
    )

    cursor.execute(
        """
        UPDATE documents
        SET
            last_seen_at = ?,
            current_version = ?
        WHERE document_id = ?
        """,
        (
            ingestion_time,
            new_version,
            document_id
        )
    )

    return "updated", document_id, ticker


# ============================================================
# REGISTER EVENTS
# ============================================================

def register_event(
    connection,
    path,
    ticker,
    ingestion_time
):

    event_id = detect_event(
        path,
        ticker
    )

    if not event_id:
        return

    cursor = connection.cursor()

    event_type = "synthetic_event"

    cursor.execute(
        """
        INSERT OR IGNORE INTO events (
            event_id,
            ticker,
            company,
            sector,
            event_type,
            event_date,
            created_at,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            ticker,
            COMPANIES[ticker]["company"],
            COMPANIES[ticker]["sector"],
            event_type,
            None,
            ingestion_time,
            "active"
        )
    )

    document_id = generate_document_id(path)

    cursor.execute(
        """
        INSERT OR IGNORE INTO document_event_links (
            document_id,
            event_id,
            relationship_type,
            confidence,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            document_id,
            event_id,
            "event_evidence",
            1.0,
            ingestion_time
        )
    )


# ============================================================
# EXPORT JSON MANIFEST
# ============================================================

def export_manifest(connection):

    cursor = connection.cursor()

    documents = []

    rows = cursor.execute(
        """
        SELECT
            document_id,
            source_path,
            filename,
            source_type,
            ticker,
            company,
            sector,
            document_type,
            first_seen_at,
            last_seen_at,
            current_version,
            status
        FROM documents
        ORDER BY source_path
        """
    ).fetchall()

    for row in rows:

        documents.append(
            {
                "document_id": row[0],
                "source_path": row[1],
                "filename": row[2],
                "source_type": row[3],
                "ticker": row[4],
                "company": row[5],
                "sector": row[6],
                "document_type": row[7],
                "first_seen_at": row[8],
                "last_seen_at": row[9],
                "current_version": row[10],
                "status": row[11]
            }
        )

    events = []

    rows = cursor.execute(
        """
        SELECT
            event_id,
            ticker,
            company,
            sector,
            event_type,
            event_date,
            status
        FROM events
        ORDER BY event_id
        """
    ).fetchall()

    for row in rows:

        events.append(
            {
                "event_id": row[0],
                "ticker": row[1],
                "company": row[2],
                "sector": row[3],
                "event_type": row[4],
                "event_date": row[5],
                "status": row[6]
            }
        )

    relationships = []

    rows = cursor.execute(
        """
        SELECT
            document_id,
            event_id,
            relationship_type,
            confidence,
            created_at
        FROM document_event_links
        ORDER BY event_id, document_id
        """
    ).fetchall()

    for row in rows:

        relationships.append(
            {
                "document_id": row[0],
                "event_id": row[1],
                "relationship_type": row[2],
                "confidence": row[3],
                "created_at": row[4]
            }
        )

    manifest = {

        "manifest_version": "2.0",

        "generated_at": datetime.now().isoformat(),

        "registry_type": "incremental_sqlite_registry",

        "synthetic_dataset": True,

        "documents": documents,

        "events": events,

        "document_event_links": relationships,

        "statistics": {
            "documents": len(documents),
            "events": len(events),
            "relationships": len(relationships)
        }
    }

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        MANIFEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# MAIN INGESTION RUN
# ============================================================

def main():

    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        REGISTRY_DB
    )

    initialize_database(connection)

    started_at = datetime.now().isoformat()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO ingestion_runs (
            started_at,
            status
        )
        VALUES (?, ?)
        """,
        (
            started_at,
            "running"
        )
    )

    ingestion_run_id = cursor.lastrowid

    connection.commit()

    files = discover_files()

    new_count = 0
    updated_count = 0
    unchanged_count = 0
    error_count = 0

    print()
    print("=" * 70)
    print("INCREMENTAL SOURCE REGISTRY")
    print("=" * 70)
    print()
    print(f"Files discovered: {len(files)}")
    print()

    for path in files:

        try:

            status, document_id, ticker = register_document(
                connection,
                path,
                started_at
            )

            register_event(
                connection,
                path,
                ticker,
                started_at
            )

            if status == "new":

                new_count += 1
                print(f"[NEW]       {path.name}")

            elif status == "updated":

                updated_count += 1
                print(f"[UPDATED]   {path.name}")

            else:

                unchanged_count += 1
                print(f"[UNCHANGED] {path.name}")

        except Exception as error:

            error_count += 1

            print(
                f"[ERROR]     {path.name}: {error}"
            )

    completed_at = datetime.now().isoformat()

    cursor.execute(
        """
        UPDATE ingestion_runs
        SET
            completed_at = ?,
            status = ?,
            discovered_count = ?,
            new_count = ?,
            updated_count = ?,
            unchanged_count = ?,
            error_count = ?
        WHERE ingestion_run_id = ?
        """,
        (
            completed_at,
            "completed" if error_count == 0 else "completed_with_errors",
            len(files),
            new_count,
            updated_count,
            unchanged_count,
            error_count,
            ingestion_run_id
        )
    )

    connection.commit()

    export_manifest(connection)

    connection.close()

    print()
    print("-" * 70)
    print("INGESTION SUMMARY")
    print("-" * 70)

    print(f"New:       {new_count}")
    print(f"Updated:   {updated_count}")
    print(f"Unchanged: {unchanged_count}")
    print(f"Errors:    {error_count}")

    print()
    print(f"Registry:  {REGISTRY_DB}")
    print(f"Manifest:  {MANIFEST_FILE}")

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()