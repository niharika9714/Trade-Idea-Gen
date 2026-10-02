from pathlib import Path
import json

# ============================================================
# Project root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent


# ============================================================
# Folder structure
# ============================================================

DIRECTORIES = [
    # -------------------------
    # Data
    # -------------------------
    "data/documents/pdf/company",
    "data/documents/pdf/sector",

    "data/documents/pptx/company",
    "data/documents/pptx/sector",

    "data/documents/docx/company",
    "data/documents/docx/sector",

    "data/documents/outlook/emails",
    "data/documents/outlook/attachments",

    "data/news/source_json",
    "data/news/stored_xml",

    "data/market_data",

    "data/internal_api/responses",

    "data/reference",

    # -------------------------
    # Source code
    # -------------------------
    "src/data_generation",
    "src/data_access",
    "src/tools",
    "src/agents",
    "src/provenance",
    "src/utils",

    # -------------------------
    # Tests / configuration
    # -------------------------
    "tests",
    "config",
    "notebooks",
    "scripts",
]


# ============================================================
# Top-level files
# ============================================================

FILES = [
    ".gitignore",
    ".env",
    "requirements.txt",
    "README.md",

    # Reference metadata
    "data/reference/companies.json",
    "data/reference/sectors.json",
    "data/reference/instruments.json",
    "data/reference/document_manifest.json",
]


# ============================================================
# Create directories
# ============================================================

print("\nCreating project structure...\n")

for directory in DIRECTORIES:
    path = PROJECT_ROOT / directory
    path.mkdir(parents=True, exist_ok=True)
    print(f"[DIR]  {path.relative_to(PROJECT_ROOT)}")


# ============================================================
# Create basic files
# ============================================================

for filename in FILES:
    path = PROJECT_ROOT / filename

    if not path.exists():

        if filename.endswith(".json"):
            path.write_text(
                "[]\n",
                encoding="utf-8"
            )

        elif filename == ".gitignore":
            path.write_text(
                """# Python
__pycache__/
*.py[cod]
*.pyo

# Virtual environment
.venv/
venv/

# Environment variables
.env

# Jupyter
.ipynb_checkpoints/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Generated databases
*.db
*.sqlite
*.sqlite3

# Temporary files
*.tmp
*.temp

# Generated logs
*.log
""",
                encoding="utf-8"
            )

        elif filename == "requirements.txt":
            path.write_text(
                """# Core
python-dotenv

# Data
pandas
numpy

# Documents
pypdf
python-docx
python-pptx
openpyxl

# Outlook / email
extract-msg

# XML / JSON
lxml

# Database
sqlalchemy

# Charts
matplotlib

# Utilities
faker
""",
                encoding="utf-8"
            )

        elif filename == "README.md":
            path.write_text(
                """# AI Investment Research Platform

Synthetic investment-research chatbot prototype.

The project demonstrates an agentic architecture where the AI
retrieves evidence directly from native data sources rather than
depending on mandatory document chunking, embeddings, or a vector DB.

## Planned data sources

- PDF research reports
- PowerPoint presentations
- Word documents
- Outlook emails
- Email attachments
- News stored as XML
- End-of-day market data in SQL
- Internal pricing / valuation API responses

## Planned architecture

User Query
    ↓
Agent / LLM
    ↓
Tool Selection
    ↓
Native Data Sources
    ↓
Evidence + Provenance
    ↓
Calculations / Reasoning
    ↓
Answer + Citations

All generated research data will be explicitly synthetic.
""",
                encoding="utf-8"
            )

        elif filename == ".env":
            path.write_text(
                "# Environment-specific configuration will be added later.\n",
                encoding="utf-8"
            )

        print(f"[FILE] {path.relative_to(PROJECT_ROOT)}")

    else:
        print(f"[SKIP] {path.relative_to(PROJECT_ROOT)} already exists")


# ============================================================
# Create placeholder metadata
# ============================================================

companies = [
    {
        "company_id": "COMP-001",
        "name": "DBS Group",
        "ticker": "D05",
        "sector": "Singapore Banks",
        "synthetic": True
    },
    {
        "company_id": "COMP-002",
        "name": "OCBC",
        "ticker": "O39",
        "sector": "Singapore Banks",
        "synthetic": True
    },
    {
        "company_id": "COMP-003",
        "name": "UOB",
        "ticker": "U11",
        "sector": "Singapore Banks",
        "synthetic": True
    },
    {
        "company_id": "COMP-004",
        "name": "HSBC",
        "ticker": "HSBA",
        "sector": "Global Banks",
        "synthetic": True
    },
    {
        "company_id": "COMP-005",
        "name": "Standard Chartered",
        "ticker": "STAN",
        "sector": "Global Banks",
        "synthetic": True
    }
]

sectors = [
    {
        "sector_id": "SEC-001",
        "name": "Singapore Banks",
        "description": "Synthetic Singapore banking sector dataset",
        "synthetic": True
    },
    {
        "sector_id": "SEC-002",
        "name": "Global Banks",
        "description": "Synthetic global banking sector dataset",
        "synthetic": True
    }
]

instruments = [
    {
        "instrument_id": "INST-001",
        "ticker": "D05",
        "company_id": "COMP-001",
        "currency": "SGD",
        "instrument_type": "EQUITY",
        "synthetic": True
    },
    {
        "instrument_id": "INST-002",
        "ticker": "O39",
        "company_id": "COMP-002",
        "currency": "SGD",
        "instrument_type": "EQUITY",
        "synthetic": True
    },
    {
        "instrument_id": "INST-003",
        "ticker": "U11",
        "company_id": "COMP-003",
        "currency": "SGD",
        "instrument_type": "EQUITY",
        "synthetic": True
    },
    {
        "instrument_id": "INST-004",
        "ticker": "HSBA",
        "company_id": "COMP-004",
        "currency": "GBP",
        "instrument_type": "EQUITY",
        "synthetic": True
    },
    {
        "instrument_id": "INST-005",
        "ticker": "STAN",
        "company_id": "COMP-005",
        "currency": "GBP",
        "instrument_type": "EQUITY",
        "synthetic": True
    }
]

metadata_files = {
    "data/reference/companies.json": companies,
    "data/reference/sectors.json": sectors,
    "data/reference/instruments.json": instruments
}

for filename, data in metadata_files.items():
    path = PROJECT_ROOT / filename

    # Only populate if currently empty.
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        existing = []

    if not existing:
        path.write_text(
            json.dumps(data, indent=4),
            encoding="utf-8"
        )
        print(f"[META] {Path(filename)}")


# ============================================================
# Completion message
# ============================================================

print("\n" + "=" * 60)
print("PROJECT STRUCTURE CREATED SUCCESSFULLY")
print("=" * 60)

print(f"\nProject root:\n{PROJECT_ROOT}")

print("\nNext step:")
print("Step 1B - Build the synthetic investment-research universe")
print("including companies, financial metrics, research topics,")
print("document relationships and provenance IDs.\n")