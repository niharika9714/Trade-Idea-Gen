from pathlib import Path
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

JSON_DIR = (
    ROOT
    / "data"
    / "news"
    / "source_json"
)

XML_DIR = (
    ROOT
    / "data"
    / "news"
    / "stored_xml"
)

JSON_DIR.mkdir(parents=True, exist_ok=True)
XML_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SYNTHETIC NEWS DATA
# ============================================================

NEWS = [

    # ========================================================
    # DBS
    # ========================================================

    {
        "article_id": "NEWS-D05-001",
        "ticker": "D05",
        "company": "DBS Group",
        "sector": "Singapore Banks",

        "event_id": "D05-EVENT-003",

        "publication_datetime": "2025-08-08T09:15:00",
        "event_datetime": "2025-08-08T08:00:00",

        "source": "Synthetic Financial Wire",
        "author": "Synthetic Banking Correspondent",

        "article_type": "earnings",

        "headline": (
            "DBS reports stronger synthetic quarterly earnings "
            "with stable capital position"
        ),

        "summary": (
            "Synthetic results indicate continued profitability "
            "and stable capital metrics, while net interest margin "
            "shows moderate movement."
        ),

        "sentiment": "positive",

        "body": (
            "DBS Group reported a synthetic quarterly earnings "
            "update showing continued profitability. Net interest "
            "income remained resilient while the synthetic net "
            "interest margin was broadly stable. Return on equity "
            "remained elevated and the synthetic CET1 ratio stayed "
            "above the assumed internal threshold. Analysts in the "
            "synthetic research universe focused on whether the "
            "earnings trajectory justified the prevailing valuation."
        ),

        "tags": [
            "earnings",
            "net-interest-margin",
            "roe",
            "capital",
            "valuation",
        ],

        "entities": [
            "DBS Group",
            "Singapore Banks",
        ],
    },

    {
        "article_id": "NEWS-D05-002",
        "ticker": "D05",
        "company": "DBS Group",
        "sector": "Singapore Banks",

        "event_id": "D05-EVENT-003",

        "publication_datetime": "2025-08-08T12:40:00",
        "event_datetime": "2025-08-08T08:00:00",

        "source": "Synthetic Market Intelligence",
        "author": "Synthetic Markets Team",

        "article_type": "market_reaction",

        "headline": (
            "DBS shares move sharply after earnings as investors "
            "reassess valuation"
        ),

        "summary": (
            "The synthetic market reaction was driven primarily "
            "by changes in valuation expectations rather than a "
            "large deterioration in reported fundamentals."
        ),

        "sentiment": "neutral",

        "body": (
            "Following the synthetic earnings release, DBS shares "
            "experienced a significant intraday movement. The "
            "synthetic market intelligence team attributed the "
            "reaction to a combination of valuation expectations, "
            "forward earnings assumptions and positioning. "
            "The fundamental indicators themselves did not show "
            "an equivalent deterioration."
        ),

        "tags": [
            "market-reaction",
            "valuation",
            "earnings",
            "share-price",
        ],

        "entities": [
            "DBS Group",
        ],
    },

    {
        "article_id": "NEWS-D05-003",
        "ticker": "D05",
        "company": "DBS Group",
        "sector": "Singapore Banks",

        "event_id": "D05-EVENT-003",

        "publication_datetime": "2025-08-09T10:05:00",
        "event_datetime": "2025-08-08T08:00:00",

        "source": "Synthetic Equity Research",
        "author": "Synthetic Equity Analyst",

        "article_type": "analyst_commentary",

        "headline": (
            "DBS valuation remains sensitive to margin expectations"
        ),

        "summary": (
            "Synthetic analyst commentary highlights the sensitivity "
            "of bank valuation to changes in net interest margin and "
            "return on equity."
        ),

        "sentiment": "neutral",

        "body": (
            "The synthetic equity research team highlighted the "
            "relationship between net interest margin, return on "
            "equity and valuation multiples. Historical observations "
            "suggest that changes in expected profitability can lead "
            "to larger valuation adjustments than changes in current "
            "earnings alone."
        ),

        "tags": [
            "valuation",
            "nim",
            "roe",
            "analyst",
        ],

        "entities": [
            "DBS Group",
            "Singapore Banks",
        ],
    },


    # ========================================================
    # OCBC
    # ========================================================

    {
        "article_id": "NEWS-O39-001",
        "ticker": "O39",
        "company": "OCBC",
        "sector": "Singapore Banks",

        "event_id": "O39-EVENT-003",

        "publication_datetime": "2025-08-08T09:25:00",
        "event_datetime": "2025-08-08T08:00:00",

        "source": "Synthetic Financial Wire",
        "author": "Synthetic Banking Correspondent",

        "article_type": "earnings",

        "headline": (
            "OCBC synthetic earnings show resilient profitability"
        ),

        "summary": (
            "OCBC's synthetic earnings update indicates resilient "
            "profitability and capital strength."
        ),

        "sentiment": "positive",

        "body": (
            "The synthetic OCBC earnings release showed resilient "
            "profitability, stable capital metrics and continued "
            "balance-sheet strength. Investors focused on the "
            "trajectory of margins and valuation relative to peers."
        ),

        "tags": [
            "earnings",
            "profitability",
            "capital",
            "valuation",
        ],

        "entities": [
            "OCBC",
            "Singapore Banks",
        ],
    },

    {
        "article_id": "NEWS-O39-002",
        "ticker": "O39",
        "company": "OCBC",
        "sector": "Singapore Banks",

        "event_id": "O39-EVENT-003",

        "publication_datetime": "2025-08-08T13:10:00",
        "event_datetime": "2025-08-08T08:00:00",

        "source": "Synthetic Market Intelligence",
        "author": "Synthetic Markets Team",

        "article_type": "market_reaction",

        "headline": (
            "OCBC market reaction reflects changing margin expectations"
        ),

        "summary": (
            "The synthetic market reaction was associated with "
            "changes in expectations around future margins."
        ),

        "sentiment": "neutral",

        "body": (
            "OCBC shares experienced a synthetic market movement "
            "following the earnings announcement. Market commentary "
            "focused on expectations for future net interest margins "
            "and relative valuation."
        ),

        "tags": [
            "market-reaction",
            "nim",
            "valuation",
        ],

        "entities": [
            "OCBC",
        ],
    },


    # ========================================================
    # UOB
    # ========================================================

    {
        "article_id": "NEWS-U11-001",
        "ticker": "U11",
        "company": "UOB",
        "sector": "Singapore Banks",

        "event_id": "U11-EVENT-003",

        "publication_datetime": "2025-08-08T09:35:00",
        "event_datetime": "2025-08-08T08:00:00",

        "source": "Synthetic Financial Wire",
        "author": "Synthetic Banking Correspondent",

        "article_type": "earnings",

        "headline": (
            "UOB synthetic earnings maintain focus on profitability"
        ),

        "summary": (
            "Synthetic results highlight profitability, capital "
            "strength and the trajectory of net interest margin."
        ),

        "sentiment": "positive",

        "body": (
            "The synthetic UOB earnings update highlighted "
            "profitability and capital strength. Investors "
            "continued to monitor the relationship between "
            "net interest margin, return on equity and valuation."
        ),

        "tags": [
            "earnings",
            "nim",
            "roe",
            "capital",
        ],

        "entities": [
            "UOB",
            "Singapore Banks",
        ],
    },

    {
        "article_id": "NEWS-U11-002",
        "ticker": "U11",
        "company": "UOB",
        "sector": "Singapore Banks",

        "event_id": "U11-EVENT-003",

        "publication_datetime": "2025-08-08T14:05:00",
        "event_datetime": "2025-08-08T08:00:00",

        "source": "Synthetic Market Intelligence",
        "author": "Synthetic Markets Team",

        "article_type": "market_reaction",

        "headline": (
            "UOB shares react to earnings and peer valuation signals"
        ),

        "summary": (
            "The synthetic market reaction reflected both company "
            "fundamentals and broader Singapore banking sentiment."
        ),

        "sentiment": "neutral",

        "body": (
            "The synthetic market intelligence report noted that "
            "UOB's price movement reflected both company-specific "
            "earnings information and changes in peer valuation."
        ),

        "tags": [
            "market-reaction",
            "peer-comparison",
            "valuation",
        ],

        "entities": [
            "UOB",
            "Singapore Banks",
        ],
    },


    # ========================================================
    # HSBC
    # ========================================================

    {
        "article_id": "NEWS-HSBA-001",
        "ticker": "HSBA",
        "company": "HSBC",
        "sector": "Global Banks",

        "event_id": "HSBA-EVENT-003",

        "publication_datetime": "2025-08-08T10:00:00",
        "event_datetime": "2025-08-08T08:00:00",

        "source": "Synthetic Global Markets Wire",
        "author": "Synthetic Banking Correspondent",

        "article_type": "earnings",

        "headline": (
            "HSBC synthetic results highlight resilient profitability"
        ),

        "summary": (
            "Synthetic HSBC results indicate resilient profitability "
            "and continued attention to capital efficiency."
        ),

        "sentiment": "positive",

        "body": (
            "The synthetic HSBC earnings release highlighted "
            "profitability and capital efficiency. Global investors "
            "continued to assess valuation against broader banking "
            "sector conditions."
        ),

        "tags": [
            "earnings",
            "profitability",
            "capital",
            "valuation",
        ],

        "entities": [
            "HSBC",
            "Global Banks",
        ],
    },


    # ========================================================
    # STANDARD CHARTERED
    # ========================================================

    {
        "article_id": "NEWS-STAN-001",
        "ticker": "STAN",
        "company": "Standard Chartered",
        "sector": "Global Banks",

        "event_id": "STAN-EVENT-003",

        "publication_datetime": "2025-08-08T10:20:00",
        "event_datetime": "2025-08-08T08:00:00",

        "source": "Synthetic Global Markets Wire",
        "author": "Synthetic Banking Correspondent",

        "article_type": "earnings",

        "headline": (
            "Standard Chartered synthetic earnings focus on "
            "return metrics"
        ),

        "summary": (
            "Synthetic results focus on return metrics, profitability "
            "and valuation."
        ),

        "sentiment": "neutral",

        "body": (
            "The synthetic Standard Chartered earnings update "
            "focused on return metrics, profitability and valuation. "
            "The market continued to compare global banks across "
            "capital efficiency and earnings resilience."
        ),

        "tags": [
            "earnings",
            "roe",
            "valuation",
            "global-banks",
        ],

        "entities": [
            "Standard Chartered",
            "Global Banks",
        ],
    },
]


# ============================================================
# JSON GENERATION
# ============================================================

def write_json_files():

    grouped = {}

    for article in NEWS:

        ticker = article["ticker"]

        if ticker not in grouped:
            grouped[ticker] = []

        grouped[ticker].append(article)

    for ticker, articles in grouped.items():

        output = JSON_DIR / f"{ticker}_news.json"

        payload = {
            "dataset_type": "synthetic_financial_news",
            "ticker": ticker,
            "article_count": len(articles),
            "articles": articles,
        }

        with open(
            output,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                payload,
                f,
                indent=4,
            )

        print(f"JSON created: {output}")


# ============================================================
# XML GENERATION
# ============================================================

def prettify_xml(element):

    rough_string = ET.tostring(
        element,
        encoding="utf-8",
    )

    reparsed = minidom.parseString(
        rough_string
    )

    return reparsed.toprettyxml(
        indent="    "
    )


def write_xml_file(ticker, articles):

    root = ET.Element(
        "financial_news"
    )

    root.set(
        "dataset_type",
        "synthetic_financial_news",
    )

    root.set(
        "ticker",
        ticker,
    )

    for article in articles:

        article_node = ET.SubElement(
            root,
            "article",
        )

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

        metadata = ET.SubElement(
            article_node,
            "metadata",
        )

        fields = [
            "article_id",
            "ticker",
            "company",
            "sector",
            "event_id",
            "publication_datetime",
            "event_datetime",
            "source",
            "author",
            "article_type",
        ]

        for field in fields:

            node = ET.SubElement(
                metadata,
                field,
            )

            node.text = str(
                article.get(field, "")
            )

        # ----------------------------------------------------
        # Content
        # ----------------------------------------------------

        content = ET.SubElement(
            article_node,
            "content",
        )

        headline = ET.SubElement(
            content,
            "headline",
        )

        headline.text = article["headline"]

        summary = ET.SubElement(
            content,
            "summary",
        )

        summary.text = article["summary"]

        body = ET.SubElement(
            content,
            "body",
        )

        body.text = article["body"]

        sentiment = ET.SubElement(
            content,
            "sentiment",
        )

        sentiment.text = article["sentiment"]

        # ----------------------------------------------------
        # Tags
        # ----------------------------------------------------

        tags_node = ET.SubElement(
            article_node,
            "tags",
        )

        for tag in article["tags"]:

            tag_node = ET.SubElement(
                tags_node,
                "tag",
            )

            tag_node.text = tag

        # ----------------------------------------------------
        # Entities
        # ----------------------------------------------------

        entities_node = ET.SubElement(
            article_node,
            "entities",
        )

        for entity in article["entities"]:

            entity_node = ET.SubElement(
                entities_node,
                "entity",
            )

            entity_node.text = entity

    output = XML_DIR / f"{ticker}_news.xml"

    with open(
        output,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            prettify_xml(root)
        )

    print(f"XML created:  {output}")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("GENERATING SYNTHETIC FINANCIAL NEWS")
    print("=" * 70)
    print()

    write_json_files()

    grouped = {}

    for article in NEWS:

        ticker = article["ticker"]

        grouped.setdefault(
            ticker,
            [],
        ).append(article)

    for ticker, articles in grouped.items():

        write_xml_file(
            ticker,
            articles,
        )

    print()
    print("=" * 70)
    print(
        f"Generated {len(NEWS)} synthetic news articles"
    )
    print("=" * 70)

    print()
    print("JSON directory:")
    print(JSON_DIR)

    print()
    print("XML directory:")
    print(XML_DIR)


if __name__ == "__main__":
    main()