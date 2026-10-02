from pathlib import Path
from datetime import datetime

from msgforge import Message


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

EMAIL_DIR = (
    ROOT
    / "data"
    / "documents"
    / "outlook"
    / "emails"
)

EMAIL_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# COMPANY CONFIGURATION
# ============================================================

COMPANIES = {
    "D05": {
        "name": "DBS Group",
        "sector": "Singapore Banks",
        "currency": "SGD",
    },
    "O39": {
        "name": "OCBC",
        "sector": "Singapore Banks",
        "currency": "SGD",
    },
    "U11": {
        "name": "UOB",
        "sector": "Singapore Banks",
        "currency": "SGD",
    },
    "HSBA": {
        "name": "HSBC",
        "sector": "Global Banks",
        "currency": "GBP",
    },
    "STAN": {
        "name": "Standard Chartered",
        "sector": "Global Banks",
        "currency": "GBP",
    },
}


# ============================================================
# FILE HELPERS
# ============================================================

def find_file(folder: Path, filename: str) -> Path:

    matches = list(folder.rglob(filename))

    if not matches:
        raise FileNotFoundError(
            f"\nCould not find:\n{filename}\n"
            f"under:\n{folder}"
        )

    return matches[0]


def find_chart(ticker: str) -> Path:

    chart_dir = (
        ROOT
        / "data"
        / "documents"
        / "assets"
        / "charts"
    )

    filename = f"{ticker}_price_history.png"

    return find_file(chart_dir, filename)


# ============================================================
# EMAIL CREATION
# ============================================================

def create_email(
    ticker: str,
    event_id: str,
    subject: str,
    sent_time: datetime,
    body_html: str,
    attachments: list[Path],
    inline_image: Path | None = None,
):

    company = COMPANIES[ticker]

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">

        <h2>{subject}</h2>

        <div style="
            background-color:#fff3cd;
            border:1px solid #e0c36c;
            padding:10px;
            margin-bottom:15px;
        ">

            <b>SYNTHETIC INVESTMENT RESEARCH DATA</b>

            <br>

            This email is artificially generated for the
            Trade Idea Gen prototype and does not represent
            real investment research.

        </div>


        <h3>Research Metadata</h3>

        <table
            border="1"
            cellpadding="7"
            cellspacing="0"
            style="border-collapse:collapse;"
        >

            <tr>
                <td><b>Company</b></td>
                <td>{company["name"]}</td>
            </tr>

            <tr>
                <td><b>Ticker</b></td>
                <td>{ticker}</td>
            </tr>

            <tr>
                <td><b>Sector</b></td>
                <td>{company["sector"]}</td>
            </tr>

            <tr>
                <td><b>Currency</b></td>
                <td>{company["currency"]}</td>
            </tr>

            <tr>
                <td><b>Event ID</b></td>
                <td>{event_id}</td>
            </tr>

            <tr>
                <td><b>Research Date</b></td>
                <td>{sent_time.strftime("%Y-%m-%d")}</td>
            </tr>

        </table>

        <br>

        {body_html}
    """

    # --------------------------------------------------------
    # Inline image
    # --------------------------------------------------------

    if inline_image:

        html += f"""

        <h3>Historical Market Context</h3>

        <p>
            Figure 1 — Synthetic historical share-price movement.
        </p>

        <img
            src="cid:price_chart"
            width="700"
        >

        <p>
            <i>
            Figure 1: Historical price series used as
            contextual evidence for the investment discussion.
            </i>
        </p>

        """

    html += """

        <hr>

        <p>
            <i>
            Synthetic dataset — prototype / engineering
            validation only.
            </i>
        </p>

    </body>
    </html>
    """

    # --------------------------------------------------------
    # Create MSG
    # --------------------------------------------------------

    message = Message(

        subject=subject,

        html_body=html,

        sender=(
            "synthetic.research@example.com",
            "Synthetic Equity Research Desk",
        ),

        to=[
            (
                "synthetic.trading@example.com",
                "Synthetic Trading Desk",
            )
        ],

        cc=[
            (
                "synthetic.strategy@example.com",
                "Synthetic Strategy Team",
            )
        ],

        sent=sent_time,

        importance="normal",
    )

    # --------------------------------------------------------
    # Inline chart
    # --------------------------------------------------------

    if inline_image:

        message.attach(
            str(inline_image),
            content_id="price_chart",
        )

    # --------------------------------------------------------
    # Normal attachments
    # --------------------------------------------------------

    for attachment in attachments:

        if attachment.exists():

            message.attach(
                str(attachment)
            )

        else:

            print(
                f"WARNING: attachment not found: "
                f"{attachment}"
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    filename = (
        f"{ticker}_{event_id}_Investment_Update.msg"
    )

    output_path = EMAIL_DIR / filename

    message.save(str(output_path))

    print(f"Created: {output_path}")

    return output_path


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("GENERATING SYNTHETIC OUTLOOK .MSG FILES")
    print("=" * 70)
    print()

    generated = []

    # ========================================================
    # DBS
    # ========================================================

    ticker = "D05"

    pptx = find_file(
        ROOT
        / "data"
        / "documents"
        / "pptx"
        / "company",
        f"{ticker}_Earnings_Deep_Dive.pptx",
    )

    docx = find_file(
        ROOT
        / "data"
        / "documents"
        / "docx"
        / "company",
        f"{ticker}_Investment_Committee_Note.docx",
    )

    chart = find_chart(ticker)

    body = """

    <p>
        The synthetic equity research desk reviewed the latest
        earnings information and the corresponding market
        response.
    </p>

    <p>
        The analysis combines historical market data,
        profitability metrics, valuation information and
        peer comparisons.
    </p>

    <h3>Investment Context</h3>

    <p>
        The observed market movement should be evaluated against
        both the fundamental earnings trajectory and the historical
        relationship between earnings events and subsequent
        share-price performance.
    </p>

    <h3>Key Analytical Questions</h3>

    <ol>

        <li>
            Was the observed price movement consistent with
            historical earnings reactions?
        </li>

        <li>
            Did valuation multiples change materially after
            the event?
        </li>

        <li>
            How did the company perform relative to its
            Singapore banking peers?
        </li>

        <li>
            Which historical indicators provide evidence
            for or against the observed market reaction?
        </li>

    </ol>

    """

    generated.append(
        create_email(

            ticker="D05",

            event_id="D05-EVENT-003",

            subject=(
                "DBS — Q2 Earnings Reaction and "
                "Valuation Review [SYNTHETIC]"
            ),

            sent_time=datetime(
                2025,
                8,
                8,
                16,
                30,
            ),

            body_html=body,

            attachments=[
                pptx,
                docx,
            ],

            inline_image=chart,
        )
    )


    # ========================================================
    # OCBC
    # ========================================================

    ticker = "O39"

    pptx = find_file(
        ROOT
        / "data"
        / "documents"
        / "pptx"
        / "company",
        f"{ticker}_Earnings_Deep_Dive.pptx",
    )

    docx = find_file(
        ROOT
        / "data"
        / "documents"
        / "docx"
        / "company",
        f"{ticker}_Investment_Committee_Note.docx",
    )

    chart = find_chart(ticker)

    body = """

    <p>
        The synthetic research desk reviewed OCBC's latest
        earnings information and the corresponding market
        response.
    </p>

    <p>
        The analysis considers profitability, valuation,
        historical price behaviour and peer performance.
    </p>

    <h3>Key Analytical Questions</h3>

    <ul>

        <li>
            How significant was the historical market reaction?
        </li>

        <li>
            Did the fundamental indicators change materially?
        </li>

        <li>
            How does valuation compare with Singapore banking peers?
        </li>

        <li>
            Which historical observations support the interpretation?
        </li>

    </ul>

    """

    generated.append(
        create_email(

            ticker="O39",

            event_id="O39-EVENT-003",

            subject=(
                "OCBC — Earnings Review and "
                "Peer Valuation [SYNTHETIC]"
            ),

            sent_time=datetime(
                2025,
                8,
                8,
                17,
                5,
            ),

            body_html=body,

            attachments=[
                pptx,
                docx,
            ],

            inline_image=chart,
        )
    )


    # ========================================================
    # UOB
    # ========================================================

    ticker = "U11"

    pptx = find_file(
        ROOT
        / "data"
        / "documents"
        / "pptx"
        / "company",
        f"{ticker}_Earnings_Deep_Dive.pptx",
    )

    docx = find_file(
        ROOT
        / "data"
        / "documents"
        / "docx"
        / "company",
        f"{ticker}_Investment_Committee_Note.docx",
    )

    chart = find_chart(ticker)

    body = """

    <p>
        The synthetic research team reviewed UOB's historical
        earnings performance and associated market movements.
    </p>

    <p>
        The analysis focuses on profitability, capital strength,
        valuation and relative performance.
    </p>

    <h3>Analytical Focus</h3>

    <ul>

        <li>
            Net interest margin trajectory
        </li>

        <li>
            Return on equity
        </li>

        <li>
            Relative valuation
        </li>

        <li>
            Historical price reaction
        </li>

    </ul>

    """

    generated.append(
        create_email(

            ticker="U11",

            event_id="U11-EVENT-003",

            subject=(
                "UOB — Earnings and Historical "
                "Market Reaction [SYNTHETIC]"
            ),

            sent_time=datetime(
                2025,
                8,
                8,
                17,
                25,
            ),

            body_html=body,

            attachments=[
                pptx,
                docx,
            ],

            inline_image=chart,
        )
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print(
        f"Generated {len(generated)} Outlook .MSG files"
    )
    print("=" * 70)

    print()
    print("Output directory:")
    print(EMAIL_DIR)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()