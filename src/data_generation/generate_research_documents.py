from pathlib import Path
import sqlite3
import math
import shutil

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether
)

from pptx import Presentation
from pptx.util import Inches, Pt

from docx import Document
from docx.shared import Inches as DocxInches, Pt as DocxPt


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = (
    PROJECT_ROOT
    / "data"
    / "market_data"
    / "market.db"
)

DOC_ROOT = (
    PROJECT_ROOT
    / "data"
    / "documents"
)

PDF_COMPANY_DIR = DOC_ROOT / "pdf" / "company"
PDF_SECTOR_DIR = DOC_ROOT / "pdf" / "sector"

PPTX_COMPANY_DIR = DOC_ROOT / "pptx" / "company"
PPTX_SECTOR_DIR = DOC_ROOT / "pptx" / "sector"

DOCX_COMPANY_DIR = DOC_ROOT / "docx" / "company"
DOCX_SECTOR_DIR = DOC_ROOT / "docx" / "sector"

ASSET_DIR = DOC_ROOT / "assets"
CHART_DIR = ASSET_DIR / "charts"

for directory in [
    PDF_COMPANY_DIR,
    PDF_SECTOR_DIR,
    PPTX_COMPANY_DIR,
    PPTX_SECTOR_DIR,
    DOCX_COMPANY_DIR,
    DOCX_SECTOR_DIR,
    CHART_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# COMPANY CONFIGURATION
# ============================================================

COMPANIES = {
    "D05": {
        "name": "DBS Group",
        "sector": "Singapore Banks",
        "currency": "SGD"
    },
    "O39": {
        "name": "OCBC",
        "sector": "Singapore Banks",
        "currency": "SGD"
    },
    "U11": {
        "name": "UOB",
        "sector": "Singapore Banks",
        "currency": "SGD"
    },
    "HSBA": {
        "name": "HSBC",
        "sector": "Global Banks",
        "currency": "GBP"
    },
    "STAN": {
        "name": "Standard Chartered",
        "sector": "Global Banks",
        "currency": "GBP"
    }
}


# ============================================================
# HISTORICAL EVENTS
# ============================================================

EVENTS = [
    {
        "event_id": "EVENT-001",
        "date": "2024-02-15",
        "ticker": "D05",
        "title": "DBS FY2023 Earnings Release"
    },
    {
        "event_id": "EVENT-002",
        "date": "2024-05-10",
        "ticker": "D05",
        "title": "DBS Q1 2024 Earnings"
    },
    {
        "event_id": "EVENT-003",
        "date": "2024-08-08",
        "ticker": "D05",
        "title": "DBS Q2 2024 Earnings"
    },
    {
        "event_id": "EVENT-004",
        "date": "2024-11-07",
        "ticker": "D05",
        "title": "DBS Q3 2024 Earnings"
    },
    {
        "event_id": "EVENT-005",
        "date": "2025-02-14",
        "ticker": "D05",
        "title": "DBS FY2024 Earnings"
    },
    {
        "event_id": "EVENT-006",
        "date": "2025-05-09",
        "ticker": "D05",
        "title": "DBS Q1 2025 Earnings"
    },
    {
        "event_id": "EVENT-007",
        "date": "2025-08-08",
        "ticker": "D05",
        "title": "DBS Q2 2025 Earnings"
    },
    {
        "event_id": "EVENT-008",
        "date": "2025-11-06",
        "ticker": "D05",
        "title": "DBS Q3 2025 Earnings"
    },
    {
        "event_id": "EVENT-009",
        "date": "2026-02-13",
        "ticker": "D05",
        "title": "DBS FY2025 Earnings"
    },
    {
        "event_id": "EVENT-010",
        "date": "2025-09-18",
        "ticker": "D05",
        "title": "Synthetic Monetary Policy Shock"
    }
]


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def get_prices(ticker):
    conn = get_connection()

    query = """
        SELECT
            trade_date,
            close_price,
            adjusted_close,
            daily_return
        FROM daily_prices
        WHERE ticker = ?
        ORDER BY trade_date
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=[ticker]
    )

    conn.close()

    df["trade_date"] = pd.to_datetime(df["trade_date"])

    return df


def get_volume(ticker):
    conn = get_connection()

    query = """
        SELECT
            trade_date,
            volume,
            turnover
        FROM daily_volume
        WHERE ticker = ?
        ORDER BY trade_date
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=[ticker]
    )

    conn.close()

    df["trade_date"] = pd.to_datetime(df["trade_date"])

    return df


def get_fundamentals(ticker):
    conn = get_connection()

    query = """
        SELECT *
        FROM fundamentals
        WHERE ticker = ?
        ORDER BY report_date
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=[ticker]
    )

    conn.close()

    df["report_date"] = pd.to_datetime(
        df["report_date"]
    )

    return df


def get_sector_prices(sector):
    conn = get_connection()

    query = """
        SELECT
            trade_date,
            close_price,
            daily_return
        FROM sector_prices
        WHERE sector = ?
        ORDER BY trade_date
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=[sector]
    )

    conn.close()

    df["trade_date"] = pd.to_datetime(
        df["trade_date"]
    )

    return df


def get_latest_fundamentals(ticker):

    df = get_fundamentals(ticker)

    return df.iloc[-1]


# ============================================================
# CALCULATIONS
# ============================================================

def calculate_return(df, days):

    if len(df) < days + 1:
        return np.nan

    start = df.iloc[-days - 1]["close_price"]
    end = df.iloc[-1]["close_price"]

    return (end / start - 1) * 100


def calculate_max_drawdown(df):

    prices = df["close_price"]

    rolling_max = prices.cummax()

    drawdown = (
        prices / rolling_max
        - 1
    )

    return drawdown.min() * 100


def calculate_event_return(
    df,
    event_date,
    window=1
):

    event_date = pd.Timestamp(event_date)

    matching = df[
        df["trade_date"] == event_date
    ]

    if matching.empty:
        return None

    index = matching.index[0]

    if index - window < 0:
        return None

    before = df.loc[
        index - window,
        "close_price"
    ]

    after = df.loc[
        index,
        "close_price"
    ]

    return (
        after / before - 1
    ) * 100


# ============================================================
# CHART GENERATION
# ============================================================

def save_price_chart(ticker):

    company = COMPANIES[ticker]

    df = get_prices(ticker)

    fig, ax = plt.subplots(
        figsize=(10, 4.8)
    )

    ax.plot(
        df["trade_date"],
        df["close_price"]
    )

    ax.set_title(
        f"{company['name']} Synthetic Share Price"
    )

    ax.set_xlabel("Date")
    ax.set_ylabel(
        f"Price ({company['currency']})"
    )

    ax.grid(
        alpha=0.25
    )

    fig.tight_layout()

    path = (
        CHART_DIR
        / f"{ticker}_price_history.png"
    )

    fig.savefig(
        path,
        dpi=160
    )

    plt.close(fig)

    return path


def save_fundamental_chart(ticker):

    company = COMPANIES[ticker]

    df = get_fundamentals(ticker)

    fig, ax = plt.subplots(
        figsize=(9, 4.5)
    )

    ax.plot(
        df["report_date"],
        df["net_interest_margin"],
        marker="o",
        label="NIM"
    )

    ax2 = ax.twinx()

    ax2.plot(
        df["report_date"],
        df["roe"],
        marker="s",
        label="ROE"
    )

    ax.set_title(
        f"{company['name']} NIM and ROE"
    )

    ax.set_ylabel("NIM (%)")
    ax2.set_ylabel("ROE (%)")

    ax.grid(
        alpha=0.25
    )

    fig.tight_layout()

    path = (
        CHART_DIR
        / f"{ticker}_nim_roe.png"
    )

    fig.savefig(
        path,
        dpi=160
    )

    plt.close(fig)

    return path


def save_volume_chart(ticker):

    company = COMPANIES[ticker]

    df = get_volume(ticker)

    fig, ax = plt.subplots(
        figsize=(10, 4)
    )

    ax.plot(
        df["trade_date"],
        df["volume"]
    )

    ax.set_title(
        f"{company['name']} Trading Volume"
    )

    ax.set_xlabel("Date")
    ax.set_ylabel("Shares")

    ax.grid(
        alpha=0.25
    )

    fig.tight_layout()

    path = (
        CHART_DIR
        / f"{ticker}_volume.png"
    )

    fig.savefig(
        path,
        dpi=160
    )

    plt.close(fig)

    return path


def save_sector_comparison_chart():

    companies = [
        "D05",
        "O39",
        "U11"
    ]

    returns = []

    for ticker in companies:

        df = get_prices(ticker)

        one_year = (
            df[
                df["trade_date"]
                >= df["trade_date"].max()
                - pd.Timedelta(days=365)
            ]
        )

        ret = (
            one_year.iloc[-1]["close_price"]
            /
            one_year.iloc[0]["close_price"]
            - 1
        ) * 100

        returns.append(
            ret
        )

    names = [
        COMPANIES[t]["name"]
        for t in companies
    ]

    fig, ax = plt.subplots(
        figsize=(8, 4.5)
    )

    ax.bar(
        names,
        returns
    )

    ax.set_title(
        "12-Month Synthetic Share Performance"
    )

    ax.set_ylabel("Return (%)")

    ax.axhline(
        0,
        linewidth=0.8
    )

    ax.grid(
        axis="y",
        alpha=0.25
    )

    fig.tight_layout()

    path = (
        CHART_DIR
        / "singapore_bank_comparison.png"
    )

    fig.savefig(
        path,
        dpi=160
    )

    plt.close(fig)

    return path


# ============================================================
# PDF HELPERS
# ============================================================

def pdf_styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=20
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=30
        )
    )

    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            fontSize=17,
            leading=22,
            spaceBefore=12,
            spaceAfter=10
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=14,
            spaceAfter=8
        )
    )

    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            spaceAfter=12
        )
    )

    return styles


def make_table(data):

    table = Table(
        data,
        repeatRows=1
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#263238")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7.5
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.grey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
        ])
    )

    return table


# ============================================================
# COMPANY PDF
# ============================================================

def generate_company_pdf(ticker):

    company = COMPANIES[ticker]

    prices = get_prices(ticker)
    fundamentals = get_fundamentals(ticker)
    volume = get_volume(ticker)

    latest = fundamentals.iloc[-1]

    price_chart = save_price_chart(ticker)
    fundamental_chart = save_fundamental_chart(ticker)
    volume_chart = save_volume_chart(ticker)

    filename = (
        f"{ticker}_Synthetic_Investment_Research_Report.pdf"
    )

    output = (
        PDF_COMPANY_DIR
        / filename
    )

    styles = pdf_styles()

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    story = []

    # --------------------------------------------------------
    # Cover
    # --------------------------------------------------------

    story.append(
        Spacer(1, 0.8 * inch)
    )

    story.append(
        Paragraph(
            company["name"],
            styles["ReportTitle"]
        )
    )

    story.append(
        Paragraph(
            "Synthetic Investment Research Report",
            styles["ReportSubtitle"]
        )
    )

    story.append(
        Paragraph(
            f"Ticker: {ticker} | "
            f"Sector: {company['sector']} | "
            f"Currency: {company['currency']}",
            styles["ReportSubtitle"]
        )
    )

    story.append(
        Spacer(1, 1.0 * inch)
    )

    story.append(
        Paragraph(
            "<b>IMPORTANT:</b> This document contains "
            "synthetic data generated for an AI investment "
            "research prototype. It is not real investment "
            "research and must not be used for investment decisions.",
            styles["BodyCustom"]
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # Executive summary
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "1. Executive Summary",
            styles["Section"]
        )
    )

    return_1y = calculate_return(
        prices,
        min(250, len(prices) - 1)
    )

    max_dd = calculate_max_drawdown(
        prices
    )

    narrative = (
        f"{company['name']} is represented in this "
        f"synthetic dataset as a {company['sector']} "
        f"company. The latest synthetic fundamental "
        f"snapshot reports a net interest margin of "
        f"{latest['net_interest_margin']:.2f}%, ROE of "
        f"{latest['roe']:.2f}%, CET1 of "
        f"{latest['cet1_ratio']:.2f}% and NPL ratio of "
        f"{latest['npl_ratio']:.2f}%."
    )

    story.append(
        Paragraph(
            narrative,
            styles["BodyCustom"]
        )
    )

    story.append(
        Paragraph(
            f"The synthetic one-year share-price return "
            f"is approximately {return_1y:.2f}%, while the "
            f"maximum historical drawdown in the generated "
            f"series is approximately {max_dd:.2f}%.",
            styles["BodyCustom"]
        )
    )

    # --------------------------------------------------------
    # KPI table
    # --------------------------------------------------------

    kpi_data = [
        [
            "Metric",
            "Value"
        ],
        [
            "Revenue",
            f"{latest['revenue']:,.0f}"
        ],
        [
            "Net Interest Income",
            f"{latest['net_interest_income']:,.0f}"
        ],
        [
            "NIM",
            f"{latest['net_interest_margin']:.2f}%"
        ],
        [
            "ROE",
            f"{latest['roe']:.2f}%"
        ],
        [
            "CET1",
            f"{latest['cet1_ratio']:.2f}%"
        ],
        [
            "NPL",
            f"{latest['npl_ratio']:.2f}%"
        ],
        [
            "P/E",
            f"{latest['pe_ratio']:.2f}x"
        ],
        [
            "P/B",
            f"{latest['pb_ratio']:.2f}x"
        ]
    ]

    story.append(
        make_table(kpi_data)
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # Price history
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "2. Historical Share Performance",
            styles["Section"]
        )
    )

    story.append(
        Image(
            str(price_chart),
            width=6.8 * inch,
            height=3.25 * inch
        )
    )

    story.append(
        Paragraph(
            "Figure 1. Synthetic daily closing-price history. "
            "Source: market.db / daily_prices.",
            styles["Caption"]
        )
    )

    # --------------------------------------------------------
    # Fundamentals
    # --------------------------------------------------------

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "3. Fundamental Performance",
            styles["Section"]
        )
    )

    story.append(
        Image(
            str(fundamental_chart),
            width=6.8 * inch,
            height=3.3 * inch
        )
    )

    story.append(
        Paragraph(
            "Figure 2. Synthetic NIM and ROE history. "
            "Source: market.db / fundamentals.",
            styles["Caption"]
        )
    )

    fundamental_table = [
        [
            "Date",
            "Revenue",
            "NIM",
            "ROE",
            "CET1",
            "NPL",
            "P/B"
        ]
    ]

    for _, row in fundamentals.tail(6).iterrows():

        fundamental_table.append([
            row["report_date"].strftime("%Y-%m-%d"),
            f"{row['revenue']:,.0f}",
            f"{row['net_interest_margin']:.2f}%",
            f"{row['roe']:.2f}%",
            f"{row['cet1_ratio']:.2f}%",
            f"{row['npl_ratio']:.2f}%",
            f"{row['pb_ratio']:.2f}x"
        ])

    story.append(
        make_table(
            fundamental_table
        )
    )

    # --------------------------------------------------------
    # Trading activity
    # --------------------------------------------------------

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "4. Trading Activity",
            styles["Section"]
        )
    )

    story.append(
        Image(
            str(volume_chart),
            width=6.8 * inch,
            height=3.1 * inch
        )
    )

    story.append(
        Paragraph(
            "Figure 3. Synthetic daily trading volume. "
            "Event dates contain deliberately generated "
            "volume spikes to support event-driven research.",
            styles["Caption"]
        )
    )

    # --------------------------------------------------------
    # Event analysis
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "5. Historical Investment Events",
            styles["Section"]
        )
    )

    event_table = [
        [
            "Event",
            "Date",
            "1-Day Price Reaction"
        ]
    ]

    company_events = [
        e for e in EVENTS
        if e["ticker"] == ticker
    ]

    for event in company_events:

        reaction = calculate_event_return(
            prices,
            event["date"]
        )

        event_table.append([
            event["event_id"],
            event["date"],
            (
                f"{reaction:.2f}%"
                if reaction is not None
                else "N/A"
            )
        ])

    story.append(
        make_table(event_table)
    )

    story.append(
        Spacer(1, 12)
    )

    story.append(
        Paragraph(
            "The event IDs above will later be reused "
            "across synthetic news articles, Outlook "
            "messages, analyst presentations and investment "
            "committee documents. This deliberately creates "
            "cross-source evidence that an agent must reconcile.",
            styles["BodyCustom"]
        )
    )

    # --------------------------------------------------------
    # Valuation
    # --------------------------------------------------------

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "6. Valuation Framework",
            styles["Section"]
        )
    )

    story.append(
        Paragraph(
            f"The latest synthetic valuation snapshot "
            f"shows a P/E ratio of "
            f"{latest['pe_ratio']:.2f}x and P/B ratio of "
            f"{latest['pb_ratio']:.2f}x. These figures are "
            f"synthetic and are intended to support "
            f"relative-value reasoning by the prototype agent.",
            styles["BodyCustom"]
        )
    )

    valuation_table = [
        [
            "Metric",
            "Latest"
        ],
        [
            "EPS",
            f"{latest['eps']:.3f}"
        ],
        [
            "Book Value / Share",
            f"{latest['book_value_per_share']:.3f}"
        ],
        [
            "P/E",
            f"{latest['pe_ratio']:.2f}x"
        ],
        [
            "P/B",
            f"{latest['pb_ratio']:.2f}x"
        ],
        [
            "ROE",
            f"{latest['roe']:.2f}%"
        ]
    ]

    story.append(
        make_table(
            valuation_table
        )
    )

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "7. Key Risks and Research Questions",
            styles["Section"]
        )
    )

    risks = [
        "Sensitivity of NIM to changes in the interest-rate environment.",
        "Potential deterioration in asset quality and NPLs.",
        "Changes in loan and deposit growth.",
        "Valuation compression despite stable profitability.",
        "Sector-wide market movements obscuring company-specific performance.",
        "Event-driven volatility around earnings announcements."
    ]

    for risk in risks:

        story.append(
            Paragraph(
                f"• {risk}",
                styles["BodyCustom"]
            )
        )

    # --------------------------------------------------------
    # Data provenance
    # --------------------------------------------------------

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "8. Data Provenance",
            styles["Section"]
        )
    )

    provenance = [
        [
            "Evidence Type",
            "Source"
        ],
        [
            "Daily prices",
            "market.db / daily_prices"
        ],
        [
            "Trading volume",
            "market.db / daily_volume"
        ],
        [
            "Fundamentals",
            "market.db / fundamentals"
        ],
        [
            "Historical events",
            "data/reference/events.json"
        ],
        [
            "Synthetic status",
            "Synthetic dataset"
        ]
    ]

    story.append(
        make_table(
            provenance
        )
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "This report is deliberately designed to "
            "contain multiple semantic relationships between "
            "narrative, tables, charts, dates and events. "
            "Future ingestion logic should preserve those "
            "relationships rather than flattening the report "
            "into arbitrary text chunks.",
            styles["BodyCustom"]
        )
    )

    doc.build(story)

    print(
        f"Created PDF: {output}"
    )


# ============================================================
# SECTOR PDF
# ============================================================

def generate_sector_pdf():

    output = (
        PDF_SECTOR_DIR
        / "Singapore_Banks_Synthetic_Sector_Review.pdf"
    )

    chart = save_sector_comparison_chart()

    styles = pdf_styles()

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    story = []

    story.append(
        Spacer(1, 0.8 * inch)
    )

    story.append(
        Paragraph(
            "Singapore Banks",
            styles["ReportTitle"]
        )
    )

    story.append(
        Paragraph(
            "Synthetic Sector Investment Research",
            styles["ReportSubtitle"]
        )
    )

    story.append(
        Paragraph(
            "DBS Group | OCBC | UOB",
            styles["ReportSubtitle"]
        )
    )

    story.append(
        Paragraph(
            "<b>SYNTHETIC DATA NOTICE:</b> "
            "This report is generated solely for testing "
            "an AI investment research platform.",
            styles["BodyCustom"]
        )
    )

    story.append(PageBreak())

    story.append(
        Paragraph(
            "1. Sector Overview",
            styles["Section"]
        )
    )

    story.append(
        Paragraph(
            "The synthetic Singapore banking universe "
            "contains three large-cap banking institutions. "
            "The dataset is deliberately structured to "
            "support relative-performance, profitability, "
            "capital and valuation analysis.",
            styles["BodyCustom"]
        )
    )

    story.append(
        Image(
            str(chart),
            width=6.8 * inch,
            height=3.8 * inch
        )
    )

    story.append(
        Paragraph(
            "Figure 1. Synthetic 12-month share performance.",
            styles["Caption"]
        )
    )

    # --------------------------------------------------------
    # Comparison table
    # --------------------------------------------------------

    latest = {}

    for ticker in [
        "D05",
        "O39",
        "U11"
    ]:
        latest[ticker] = get_latest_fundamentals(
            ticker
        )

    table = [
        [
            "Company",
            "NIM",
            "ROE",
            "CET1",
            "NPL",
            "P/E",
            "P/B"
        ]
    ]

    for ticker in [
        "D05",
        "O39",
        "U11"
    ]:

        row = latest[ticker]

        table.append([
            COMPANIES[ticker]["name"],
            f"{row['net_interest_margin']:.2f}%",
            f"{row['roe']:.2f}%",
            f"{row['cet1_ratio']:.2f}%",
            f"{row['npl_ratio']:.2f}%",
            f"{row['pe_ratio']:.2f}x",
            f"{row['pb_ratio']:.2f}x"
        ])

    story.append(
        make_table(table)
    )

    story.append(PageBreak())

    story.append(
        Paragraph(
            "2. Relative-Value Research Questions",
            styles["Section"]
        )
    )

    questions = [
        "Which company combines the highest ROE with the lowest valuation multiple?",
        "Does higher NIM translate into superior share-price performance?",
        "How does capital strength differ across the three institutions?",
        "Did earnings-event volatility differ between companies?",
        "Does relative valuation explain differences in subsequent returns?",
        "Which company has the largest sensitivity to sector-wide shocks?"
    ]

    for question in questions:

        story.append(
            Paragraph(
                f"• {question}",
                styles["BodyCustom"]
            )
        )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "These questions are intentionally designed "
            "for the future agent to answer by combining "
            "SQL data with narrative research documents.",
            styles["BodyCustom"]
        )
    )

    doc.build(story)

    print(
        f"Created sector PDF: {output}"
    )


# ============================================================
# POWERPOINT
# ============================================================

def add_title_slide(
    prs,
    title,
    subtitle
):

    slide = prs.slides.add_slide(
        prs.slide_layouts[0]
    )

    slide.shapes.title.text = title

    slide.placeholders[1].text = subtitle

    return slide


def add_text_slide(
    prs,
    title,
    bullets
):

    slide = prs.slides.add_slide(
        prs.slide_layouts[1]
    )

    slide.shapes.title.text = title

    body = slide.placeholders[1]

    body.text = bullets[0]

    for bullet in bullets[1:]:

        paragraph = body.text_frame.add_paragraph()

        paragraph.text = bullet
        paragraph.level = 0

    return slide


def add_chart_slide(
    prs,
    title,
    chart_path,
    caption
):

    slide = prs.slides.add_slide(
        prs.slide_layouts[5]
    )

    slide.shapes.title.text = title

    slide.shapes.add_picture(
        str(chart_path),
        Inches(0.7),
        Inches(1.3),
        width=Inches(8.8)
    )

    textbox = slide.shapes.add_textbox(
        Inches(0.7),
        Inches(6.6),
        Inches(8.8),
        Inches(0.5)
    )

    textbox.text_frame.text = caption

    return slide


def add_table_slide(
    prs,
    title,
    dataframe
):

    slide = prs.slides.add_slide(
        prs.slide_layouts[5]
    )

    slide.shapes.title.text = title

    rows = len(dataframe) + 1
    cols = len(dataframe.columns)

    table_shape = slide.shapes.add_table(
        rows,
        cols,
        Inches(0.5),
        Inches(1.5),
        Inches(9.0),
        Inches(4.5)
    )

    table = table_shape.table

    for col, name in enumerate(
        dataframe.columns
    ):
        table.cell(
            0,
            col
        ).text = str(name)

    for row_index, row in enumerate(
        dataframe.itertuples(index=False),
        start=1
    ):

        for col_index, value in enumerate(
            row
        ):

            table.cell(
                row_index,
                col_index
            ).text = str(value)

    return slide


def generate_company_pptx(ticker):

    company = COMPANIES[ticker]

    prs = Presentation()

    price_chart = save_price_chart(ticker)
    fundamental_chart = save_fundamental_chart(ticker)
    volume_chart = save_volume_chart(ticker)

    latest = get_latest_fundamentals(ticker)

    add_title_slide(
        prs,
        f"{company['name']} — Earnings Deep Dive",
        "Synthetic Investment Research | Prototype Dataset"
    )

    add_text_slide(
        prs,
        "Executive Summary",
        [
            f"{company['name']} ({ticker}) — synthetic research case",
            f"Latest NIM: {latest['net_interest_margin']:.2f}%",
            f"Latest ROE: {latest['roe']:.2f}%",
            f"CET1 ratio: {latest['cet1_ratio']:.2f}%",
            f"P/B: {latest['pb_ratio']:.2f}x",
            "All numbers are synthetic."
        ]
    )

    add_chart_slide(
        prs,
        "Historical Share Performance",
        price_chart,
        "Source: synthetic market.db / daily_prices"
    )

    add_chart_slide(
        prs,
        "NIM and ROE",
        fundamental_chart,
        "Source: synthetic market.db / fundamentals"
    )

    add_chart_slide(
        prs,
        "Trading Activity",
        volume_chart,
        "Event dates contain synthetic volume spikes."
    )

    fundamentals = get_fundamentals(ticker).tail(5)

    comparison = fundamentals[
        [
            "report_date",
            "revenue",
            "net_interest_margin",
            "roe",
            "cet1_ratio",
            "npl_ratio",
            "pe_ratio",
            "pb_ratio"
        ]
    ].copy()

    comparison["report_date"] = (
        comparison["report_date"]
        .dt.strftime("%Y-%m-%d")
    )

    comparison.columns = [
        "Date",
        "Revenue",
        "NIM",
        "ROE",
        "CET1",
        "NPL",
        "P/E",
        "P/B"
    ]

    add_table_slide(
        prs,
        "Latest Fundamental Snapshot",
        comparison
    )

    add_text_slide(
        prs,
        "Historical Event Map",
        [
            "EVENT-001 — FY2023 earnings",
            "EVENT-002 — Q1 2024 earnings",
            "EVENT-003 — Q2 2024 earnings",
            "EVENT-004 — Q3 2024 earnings",
            "EVENT-005 — FY2024 earnings",
            "EVENT-006 — Q1 2025 earnings",
            "EVENT-007 — Q2 2025 earnings",
            "EVENT-008 — Q3 2025 earnings",
            "EVENT-009 — FY2025 earnings",
            "EVENT-010 — synthetic monetary-policy shock"
        ]
    )

    add_text_slide(
        prs,
        "Research Questions",
        [
            "Was the post-earnings share-price movement consistent with fundamentals?",
            "How did trading volume change around the event?",
            "How does valuation compare with sector peers?",
            "Did NIM and ROE trends support the market reaction?",
            "What additional evidence should an investment agent retrieve?"
        ]
    )

    add_text_slide(
        prs,
        "Data Provenance",
        [
            "Prices → market.db / daily_prices",
            "Volume → market.db / daily_volume",
            "Fundamentals → market.db / fundamentals",
            "Events → data/reference/events.json",
            "Document status → synthetic",
            "Future versions will link this presentation to Outlook, news XML and API evidence."
        ]
    )

    output = (
        PPTX_COMPANY_DIR
        / f"{ticker}_Earnings_Deep_Dive.pptx"
    )

    prs.save(output)

    print(
        f"Created PPTX: {output}"
    )


# ============================================================
# SECTOR POWERPOINT
# ============================================================

def generate_sector_pptx():

    prs = Presentation()

    chart = save_sector_comparison_chart()

    add_title_slide(
        prs,
        "Singapore Banks — Sector Comparison",
        "Synthetic Investment Research"
    )

    add_text_slide(
        prs,
        "Sector Thesis Framework",
        [
            "Compare profitability",
            "Compare capital strength",
            "Compare asset quality",
            "Compare valuation",
            "Compare share-price performance",
            "Connect market reaction to historical events"
        ]
    )

    add_chart_slide(
        prs,
        "Relative Share Performance",
        chart,
        "Synthetic 12-month return comparison."
    )

    rows = []

    for ticker in [
        "D05",
        "O39",
        "U11"
    ]:

        f = get_latest_fundamentals(
            ticker
        )

        rows.append([
            COMPANIES[ticker]["name"],
            f"{f['net_interest_margin']:.2f}%",
            f"{f['roe']:.2f}%",
            f"{f['cet1_ratio']:.2f}%",
            f"{f['npl_ratio']:.2f}%",
            f"{f['pe_ratio']:.2f}x",
            f"{f['pb_ratio']:.2f}x"
        ])

    df = pd.DataFrame(
        rows,
        columns=[
            "Company",
            "NIM",
            "ROE",
            "CET1",
            "NPL",
            "P/E",
            "P/B"
        ]
    )

    add_table_slide(
        prs,
        "Relative Fundamental Positioning",
        df
    )

    add_text_slide(
        prs,
        "Agentic Research Questions",
        [
            "Which company has the strongest combination of profitability and capital?",
            "Does valuation compensate for differences in profitability?",
            "How did each company respond to earnings events?",
            "Which conclusions require market data versus narrative evidence?"
        ]
    )

    output = (
        PPTX_SECTOR_DIR
        / "Singapore_Banks_Sector_Comparison.pptx"
    )

    prs.save(output)

    print(
        f"Created sector PPTX: {output}"
    )


# ============================================================
# DOCX
# ============================================================

def add_docx_heading(
    document,
    text,
    level=1
):

    document.add_heading(
        text,
        level=level
    )


def add_docx_table(
    document,
    data
):

    rows = len(data)
    cols = len(data[0])

    table = document.add_table(
        rows=rows,
        cols=cols
    )

    table.style = "Table Grid"

    for r in range(rows):

        for c in range(cols):

            table.cell(
                r,
                c
            ).text = str(
                data[r][c]
            )

    return table


def generate_company_docx(ticker):

    company = COMPANIES[ticker]

    document = Document()

    title = document.add_heading(
        company["name"],
        level=0
    )

    subtitle = document.add_paragraph(
        "Synthetic Internal Investment Committee Note"
    )

    subtitle.runs[0].bold = True

    document.add_paragraph(
        f"Ticker: {ticker} | "
        f"Sector: {company['sector']} | "
        f"Currency: {company['currency']}"
    )

    document.add_paragraph(
        "SYNTHETIC DATASET — FOR AI PROTOTYPE TESTING ONLY."
    )

    add_docx_heading(
        document,
        "1. Investment Context"
    )

    document.add_paragraph(
        f"This synthetic investment note evaluates "
        f"{company['name']} using market data, fundamental "
        f"metrics and historical investment events. "
        f"The purpose is to test whether an AI research "
        f"agent can connect structured and unstructured "
        f"evidence."
    )

    prices = get_prices(ticker)
    fundamentals = get_fundamentals(ticker)

    latest = fundamentals.iloc[-1]

    add_docx_heading(
        document,
        "2. Key Metrics"
    )

    metrics = [
        ["Metric", "Latest Value"],
        ["NIM", f"{latest['net_interest_margin']:.2f}%"],
        ["ROE", f"{latest['roe']:.2f}%"],
        ["CET1", f"{latest['cet1_ratio']:.2f}%"],
        ["NPL", f"{latest['npl_ratio']:.2f}%"],
        ["P/E", f"{latest['pe_ratio']:.2f}x"],
        ["P/B", f"{latest['pb_ratio']:.2f}x"],
    ]

    add_docx_table(
        document,
        metrics
    )

    add_docx_heading(
        document,
        "3. Price Performance"
    )

    chart = save_price_chart(ticker)

    document.add_picture(
        str(chart),
        width=DocxInches(6.2)
    )

    document.add_paragraph(
        "Figure 1. Synthetic share-price history. "
        "Source: market.db / daily_prices."
    )

    add_docx_heading(
        document,
        "4. Fundamental Trend"
    )

    chart = save_fundamental_chart(ticker)

    document.add_picture(
        str(chart),
        width=DocxInches(6.2)
    )

    document.add_paragraph(
        "Figure 2. Synthetic NIM and ROE trend. "
        "Source: market.db / fundamentals."
    )

    add_docx_heading(
        document,
        "5. Event Analysis"
    )

    document.add_paragraph(
        "The following events are deliberately aligned "
        "with market-price shocks and will later appear "
        "in other document formats."
    )

    events_table = [
        [
            "Event ID",
            "Date",
            "Description"
        ]
    ]

    for event in EVENTS:

        if event["ticker"] != ticker:
            continue

        events_table.append([
            event["event_id"],
            event["date"],
            event["title"]
        ])

    add_docx_table(
        document,
        events_table
    )

    add_docx_heading(
        document,
        "6. Analyst Questions"
    )

    questions = [
        "Was the market reaction justified by the earnings trajectory?",
        "Did valuation change materially around the event?",
        "Did volume confirm unusual investor activity?",
        "How does the company compare with its sector peers?",
        "What additional evidence should the research agent retrieve?"
    ]

    for question in questions:

        document.add_paragraph(
            question,
            style="List Bullet"
        )

    add_docx_heading(
        document,
        "7. Provenance"
    )

    provenance = [
        ["Evidence", "Location"],
        ["Prices", "market.db / daily_prices"],
        ["Volume", "market.db / daily_volume"],
        ["Fundamentals", "market.db / fundamentals"],
        ["Events", "data/reference/events.json"],
        ["Dataset status", "Synthetic"]
    ]

    add_docx_table(
        document,
        provenance
    )

    output = (
        DOCX_COMPANY_DIR
        / f"{ticker}_Investment_Committee_Note.docx"
    )

    document.save(output)

    print(
        f"Created DOCX: {output}"
    )


# ============================================================
# SECTOR DOCX
# ============================================================

def generate_sector_docx():

    document = Document()

    document.add_heading(
        "Singapore Banks",
        level=0
    )

    document.add_paragraph(
        "Synthetic Sector Investment Committee Note"
    )

    document.add_paragraph(
        "DBS Group | OCBC | UOB"
    )

    document.add_paragraph(
        "SYNTHETIC DATASET — FOR AI PROTOTYPE TESTING ONLY."
    )

    add_docx_heading(
        document,
        "1. Sector Comparison"
    )

    rows = [
        [
            "Company",
            "NIM",
            "ROE",
            "CET1",
            "NPL",
            "P/E",
            "P/B"
        ]
    ]

    for ticker in [
        "D05",
        "O39",
        "U11"
    ]:

        f = get_latest_fundamentals(
            ticker
        )

        rows.append([
            COMPANIES[ticker]["name"],
            f"{f['net_interest_margin']:.2f}%",
            f"{f['roe']:.2f}%",
            f"{f['cet1_ratio']:.2f}%",
            f"{f['npl_ratio']:.2f}%",
            f"{f['pe_ratio']:.2f}x",
            f"{f['pb_ratio']:.2f}x"
        ])

    add_docx_table(
        document,
        rows
    )

    add_docx_heading(
        document,
        "2. Relative Performance"
    )

    chart = save_sector_comparison_chart()

    document.add_picture(
        str(chart),
        width=DocxInches(6.2)
    )

    document.add_paragraph(
        "Figure 1. Synthetic 12-month share-price comparison."
    )

    add_docx_heading(
        document,
        "3. Research Framework"
    )

    for item in [
        "Profitability versus valuation",
        "Capital strength versus growth",
        "Credit quality versus returns",
        "Event-driven share-price reaction",
        "Sector versus company-specific effects"
    ]:

        document.add_paragraph(
            item,
            style="List Bullet"
        )

    output = (
        DOCX_SECTOR_DIR
        / "Singapore_Banks_Sector_Review.docx"
    )

    document.save(output)

    print(
        f"Created sector DOCX: {output}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n==============================================")
    print("GENERATING SYNTHETIC RESEARCH DOCUMENTS")
    print("==============================================\n")

    print("Generating company PDFs...")

    for ticker in COMPANIES:
        generate_company_pdf(ticker)

    print("\nGenerating sector PDF...")

    generate_sector_pdf()

    print("\nGenerating company PowerPoints...")

    for ticker in COMPANIES:
        generate_company_pptx(ticker)

    print("\nGenerating sector PowerPoint...")

    generate_sector_pptx()

    print("\nGenerating company Word documents...")

    for ticker in COMPANIES:
        generate_company_docx(ticker)

    print("\nGenerating sector Word document...")

    generate_sector_docx()

    print("\n==============================================")
    print("DOCUMENT GENERATION COMPLETE")
    print("==============================================")

    print(
        "\nGenerated:"
        "\n  6 PDF reports"
        "\n  6 PowerPoint presentations"
        "\n  6 Word documents"
    )


if __name__ == "__main__":
    main()