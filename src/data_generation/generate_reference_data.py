from pathlib import Path
import json


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Synthetic Investment Universe
# ============================================================

companies = [
    {
        "company_id": "COMP-001",
        "name": "DBS Group",
        "ticker": "D05",
        "exchange": "SGX",
        "currency": "SGD",
        "sector_id": "SEC-001",
        "sector": "Singapore Banks",
        "country": "Singapore",
        "market_cap_category": "Large Cap",
        "synthetic": True
    },
    {
        "company_id": "COMP-002",
        "name": "OCBC",
        "ticker": "O39",
        "exchange": "SGX",
        "currency": "SGD",
        "sector_id": "SEC-001",
        "sector": "Singapore Banks",
        "country": "Singapore",
        "market_cap_category": "Large Cap",
        "synthetic": True
    },
    {
        "company_id": "COMP-003",
        "name": "UOB",
        "ticker": "U11",
        "exchange": "SGX",
        "currency": "SGD",
        "sector_id": "SEC-001",
        "sector": "Singapore Banks",
        "country": "Singapore",
        "market_cap_category": "Large Cap",
        "synthetic": True
    },
    {
        "company_id": "COMP-004",
        "name": "HSBC",
        "ticker": "HSBA",
        "exchange": "LSE",
        "currency": "GBP",
        "sector_id": "SEC-002",
        "sector": "Global Banks",
        "country": "United Kingdom",
        "market_cap_category": "Large Cap",
        "synthetic": True
    },
    {
        "company_id": "COMP-005",
        "name": "Standard Chartered",
        "ticker": "STAN",
        "exchange": "LSE",
        "currency": "GBP",
        "sector_id": "SEC-002",
        "sector": "Global Banks",
        "country": "United Kingdom",
        "market_cap_category": "Large Cap",
        "synthetic": True
    }
]


# ============================================================
# Sectors
# ============================================================

sectors = [
    {
        "sector_id": "SEC-001",
        "name": "Singapore Banks",
        "description": "Synthetic Singapore banking sector",
        "companies": [
            "COMP-001",
            "COMP-002",
            "COMP-003"
        ],
        "synthetic": True
    },
    {
        "sector_id": "SEC-002",
        "name": "Global Banks",
        "description": "Synthetic global banking sector",
        "companies": [
            "COMP-004",
            "COMP-005"
        ],
        "synthetic": True
    }
]


# ============================================================
# Instruments
# ============================================================

instruments = [
    {
        "instrument_id": "INST-001",
        "company_id": "COMP-001",
        "ticker": "D05",
        "instrument_type": "EQUITY",
        "currency": "SGD",
        "exchange": "SGX"
    },
    {
        "instrument_id": "INST-002",
        "company_id": "COMP-002",
        "ticker": "O39",
        "instrument_type": "EQUITY",
        "currency": "SGD",
        "exchange": "SGX"
    },
    {
        "instrument_id": "INST-003",
        "company_id": "COMP-003",
        "ticker": "U11",
        "instrument_type": "EQUITY",
        "currency": "SGD",
        "exchange": "SGX"
    },
    {
        "instrument_id": "INST-004",
        "company_id": "COMP-004",
        "ticker": "HSBA",
        "instrument_type": "EQUITY",
        "currency": "GBP",
        "exchange": "LSE"
    },
    {
        "instrument_id": "INST-005",
        "company_id": "COMP-005",
        "ticker": "STAN",
        "instrument_type": "EQUITY",
        "currency": "GBP",
        "exchange": "LSE"
    }
]


# ============================================================
# Financial metric definitions
# ============================================================

financial_metrics = [
    {
        "metric_id": "MET-001",
        "name": "Revenue",
        "category": "Income Statement",
        "unit": "million"
    },
    {
        "metric_id": "MET-002",
        "name": "Net Interest Income",
        "category": "Income Statement",
        "unit": "million"
    },
    {
        "metric_id": "MET-003",
        "name": "Net Interest Margin",
        "category": "Profitability",
        "unit": "percentage"
    },
    {
        "metric_id": "MET-004",
        "name": "ROE",
        "category": "Profitability",
        "unit": "percentage"
    },
    {
        "metric_id": "MET-005",
        "name": "ROA",
        "category": "Profitability",
        "unit": "percentage"
    },
    {
        "metric_id": "MET-006",
        "name": "Loan Growth",
        "category": "Growth",
        "unit": "percentage"
    },
    {
        "metric_id": "MET-007",
        "name": "Deposit Growth",
        "category": "Growth",
        "unit": "percentage"
    },
    {
        "metric_id": "MET-008",
        "name": "CET1 Ratio",
        "category": "Capital",
        "unit": "percentage"
    },
    {
        "metric_id": "MET-009",
        "name": "NPL Ratio",
        "category": "Credit Quality",
        "unit": "percentage"
    },
    {
        "metric_id": "MET-010",
        "name": "Credit Cost",
        "category": "Credit Quality",
        "unit": "basis_points"
    },
    {
        "metric_id": "MET-011",
        "name": "Cost-to-Income Ratio",
        "category": "Efficiency",
        "unit": "percentage"
    },
    {
        "metric_id": "MET-012",
        "name": "EPS",
        "category": "Valuation",
        "unit": "currency"
    },
    {
        "metric_id": "MET-013",
        "name": "Book Value Per Share",
        "category": "Valuation",
        "unit": "currency"
    },
    {
        "metric_id": "MET-014",
        "name": "P/E",
        "category": "Valuation",
        "unit": "multiple"
    },
    {
        "metric_id": "MET-015",
        "name": "P/B",
        "category": "Valuation",
        "unit": "multiple"
    }
]


# ============================================================
# Research topics
# ============================================================

research_topics = [
    {
        "topic_id": "TOPIC-001",
        "name": "Earnings",
        "description": "Quarterly and annual earnings performance"
    },
    {
        "topic_id": "TOPIC-002",
        "name": "Net Interest Margin",
        "description": "NIM and interest-rate sensitivity"
    },
    {
        "topic_id": "TOPIC-003",
        "name": "Credit Quality",
        "description": "NPL, provisions and credit costs"
    },
    {
        "topic_id": "TOPIC-004",
        "name": "Capital",
        "description": "CET1, capital generation and distributions"
    },
    {
        "topic_id": "TOPIC-005",
        "name": "Valuation",
        "description": "P/E, P/B, DDM and internal fair value"
    },
    {
        "topic_id": "TOPIC-006",
        "name": "Share Performance",
        "description": "Historical price and relative performance"
    },
    {
        "topic_id": "TOPIC-007",
        "name": "Macroeconomics",
        "description": "Rates, inflation, GDP and economic conditions"
    },
    {
        "topic_id": "TOPIC-008",
        "name": "Sector Comparison",
        "description": "Relative comparison between banks"
    },
    {
        "topic_id": "TOPIC-009",
        "name": "Management Commentary",
        "description": "Management outlook and strategic commentary"
    },
    {
        "topic_id": "TOPIC-010",
        "name": "Risk",
        "description": "Business, credit, market and regulatory risks"
    }
]


# ============================================================
# Historical investment events
#
# These events will later appear in:
# PDF
# PPTX
# DOCX
# Outlook
# News XML
# Market data
# ============================================================

events = [
    {
        "event_id": "EVENT-001",
        "date": "2024-02-15",
        "company_id": "COMP-001",
        "event_type": "EARNINGS",
        "title": "DBS FY2023 Earnings Release",
        "topics": [
            "TOPIC-001",
            "TOPIC-002",
            "TOPIC-004"
        ]
    },
    {
        "event_id": "EVENT-002",
        "date": "2024-05-10",
        "company_id": "COMP-001",
        "event_type": "EARNINGS",
        "title": "DBS Q1 2024 Earnings",
        "topics": [
            "TOPIC-001",
            "TOPIC-002",
            "TOPIC-003"
        ]
    },
    {
        "event_id": "EVENT-003",
        "date": "2024-08-08",
        "company_id": "COMP-001",
        "event_type": "EARNINGS",
        "title": "DBS Q2 2024 Earnings",
        "topics": [
            "TOPIC-001",
            "TOPIC-002",
            "TOPIC-005"
        ]
    },
    {
        "event_id": "EVENT-004",
        "date": "2024-11-07",
        "company_id": "COMP-001",
        "event_type": "EARNINGS",
        "title": "DBS Q3 2024 Earnings",
        "topics": [
            "TOPIC-001",
            "TOPIC-003",
            "TOPIC-004"
        ]
    },
    {
        "event_id": "EVENT-005",
        "date": "2025-02-14",
        "company_id": "COMP-001",
        "event_type": "EARNINGS",
        "title": "DBS FY2024 Earnings",
        "topics": [
            "TOPIC-001",
            "TOPIC-005",
            "TOPIC-009"
        ]
    },
    {
        "event_id": "EVENT-006",
        "date": "2025-05-09",
        "company_id": "COMP-001",
        "event_type": "EARNINGS",
        "title": "DBS Q1 2025 Earnings",
        "topics": [
            "TOPIC-001",
            "TOPIC-002",
            "TOPIC-006"
        ]
    },
    {
        "event_id": "EVENT-007",
        "date": "2025-08-08",
        "company_id": "COMP-001",
        "event_type": "EARNINGS",
        "title": "DBS Q2 2025 Earnings",
        "topics": [
            "TOPIC-001",
            "TOPIC-002",
            "TOPIC-005"
        ]
    },
    {
        "event_id": "EVENT-008",
        "date": "2025-11-06",
        "company_id": "COMP-001",
        "event_type": "EARNINGS",
        "title": "DBS Q3 2025 Earnings",
        "topics": [
            "TOPIC-001",
            "TOPIC-003",
            "TOPIC-010"
        ]
    },
    {
        "event_id": "EVENT-009",
        "date": "2026-02-13",
        "company_id": "COMP-001",
        "event_type": "EARNINGS",
        "title": "DBS FY2025 Earnings",
        "topics": [
            "TOPIC-001",
            "TOPIC-005",
            "TOPIC-009"
        ]
    },
    {
        "event_id": "EVENT-010",
        "date": "2025-09-18",
        "company_id": "COMP-001",
        "event_type": "MACRO",
        "title": "Synthetic Monetary Policy Shock",
        "topics": [
            "TOPIC-002",
            "TOPIC-007",
            "TOPIC-006"
        ]
    }
]


# ============================================================
# Relationships
# ============================================================

relationships = [
    {
        "relationship_id": "REL-001",
        "from": "COMP-001",
        "relationship": "COMPETES_WITH",
        "to": "COMP-002"
    },
    {
        "relationship_id": "REL-002",
        "from": "COMP-001",
        "relationship": "COMPETES_WITH",
        "to": "COMP-003"
    },
    {
        "relationship_id": "REL-003",
        "from": "COMP-002",
        "relationship": "COMPETES_WITH",
        "to": "COMP-003"
    },
    {
        "relationship_id": "REL-004",
        "from": "COMP-004",
        "relationship": "COMPETES_WITH",
        "to": "COMP-005"
    },
    {
        "relationship_id": "REL-005",
        "from": "SEC-001",
        "relationship": "BENCHMARKED_AGAINST",
        "to": "SEC-002"
    }
]


# ============================================================
# Save helper
# ============================================================

def save_json(filename, data):
    path = REFERENCE_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Created: {path}")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print("\nGenerating synthetic investment universe...\n")

    save_json("companies.json", companies)
    save_json("sectors.json", sectors)
    save_json("instruments.json", instruments)
    save_json("financial_metrics.json", financial_metrics)
    save_json("research_topics.json", research_topics)
    save_json("events.json", events)
    save_json("relationships.json", relationships)

    print("\nSynthetic investment universe created successfully.")
    print("\nUniverse:")
    print("  Companies :", len(companies))
    print("  Sectors   :", len(sectors))
    print("  Metrics   :", len(financial_metrics))
    print("  Topics    :", len(research_topics))
    print("  Events    :", len(events))
    print("  Relations :", len(relationships))