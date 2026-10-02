from pathlib import Path
import json
from datetime import datetime


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    ROOT
    / "data"
    / "internal_api"
    / "responses"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# SYNTHETIC COMPANY CONFIGURATION
# ============================================================

COMPANIES = {

    "D05": {
        "name": "DBS Group",
        "sector": "Singapore Banks",
        "currency": "SGD",
        "base_price": 38.50,
        "base_eps": 3.10,
        "base_book_value": 25.80,
        "base_nim": 2.15,
        "base_roe": 15.8,
    },

    "O39": {
        "name": "OCBC",
        "sector": "Singapore Banks",
        "currency": "SGD",
        "base_price": 15.20,
        "base_eps": 1.45,
        "base_book_value": 11.40,
        "base_nim": 2.05,
        "base_roe": 13.9,
    },

    "U11": {
        "name": "UOB",
        "sector": "Singapore Banks",
        "currency": "SGD",
        "base_price": 34.20,
        "base_eps": 2.85,
        "base_book_value": 24.10,
        "base_nim": 2.10,
        "base_roe": 14.5,
    },

    "HSBA": {
        "name": "HSBC",
        "sector": "Global Banks",
        "currency": "GBP",
        "base_price": 7.25,
        "base_eps": 0.82,
        "base_book_value": 6.10,
        "base_nim": 1.75,
        "base_roe": 12.7,
    },

    "STAN": {
        "name": "Standard Chartered",
        "sector": "Global Banks",
        "currency": "GBP",
        "base_price": 8.10,
        "base_eps": 0.91,
        "base_book_value": 7.05,
        "base_nim": 1.82,
        "base_roe": 11.9,
    },
}


# ============================================================
# HELPER
# ============================================================

def round_value(value, digits=4):
    return round(value, digits)


# ============================================================
# VALUATION RESPONSE
# ============================================================

def generate_valuation_response(ticker):

    company = COMPANIES[ticker]

    price = company["base_price"]
    eps = company["base_eps"]
    book_value = company["base_book_value"]

    pe = price / eps
    pb = price / book_value

    # Synthetic valuation assumptions
    target_pe = pe * 1.08
    target_pb = pb * 1.05

    pe_target_price = eps * target_pe
    pb_target_price = book_value * target_pb

    blended_target = (
        pe_target_price * 0.60
        +
        pb_target_price * 0.40
    )

    upside = (
        blended_target / price
        - 1
    ) * 100

    return {

        "api_response_type": "valuation",

        "api_version": "1.0",

        "request_id":
            f"REQ-VALUATION-{ticker}-001",

        "generated_at":
            datetime.utcnow().isoformat() + "Z",

        "company": {
            "ticker": ticker,
            "name": company["name"],
            "sector": company["sector"],
            "currency": company["currency"],
        },

        "inputs": {

            "share_price": price,

            "eps": eps,

            "book_value_per_share":
                book_value,

            "target_pe_multiplier":
                1.08,

            "target_pb_multiplier":
                1.05,

        },

        "calculations": {

            "current_pe":
                round_value(pe),

            "current_pb":
                round_value(pb),

            "pe_target_price":
                round_value(pe_target_price, 2),

            "pb_target_price":
                round_value(pb_target_price, 2),

            "blended_target_price":
                round_value(blended_target, 2),

            "implied_upside_percent":
                round_value(upside, 2),

        },

        "methodology": {

            "pe_weight": 0.60,

            "pb_weight": 0.40,

            "description":
                "Synthetic blended P/E and P/B valuation model."

        },

        "provenance": {

            "source_system":
                "Synthetic Internal Pricing Engine",

            "source_type":
                "internal_api",

            "calculation_type":
                "valuation",

            "synthetic":
                True,

        },
    }


# ============================================================
# NIM SCENARIO RESPONSE
# ============================================================

def generate_nim_scenario_response(ticker):

    company = COMPANIES[ticker]

    base_nim = company["base_nim"]

    # Synthetic scenario:
    # 50 bps NIM compression

    compression_bps = 50

    stressed_nim = (
        base_nim
        -
        compression_bps / 100
    )

    # Synthetic relationship:
    # every 10 bps NIM movement changes EPS by 1.2%

    eps_impact_percent = (
        compression_bps / 10
    ) * 1.2

    base_eps = company["base_eps"]

    stressed_eps = (
        base_eps
        *
        (1 - eps_impact_percent / 100)
    )

    return {

        "api_response_type":
            "nim_scenario",

        "api_version":
            "1.0",

        "request_id":
            f"REQ-NIM-{ticker}-001",

        "generated_at":
            datetime.utcnow().isoformat() + "Z",

        "company": {

            "ticker": ticker,

            "name":
                company["name"],

            "sector":
                company["sector"],

        },

        "scenario": {

            "scenario_name":
                "50bps NIM Compression",

            "base_nim_percent":
                base_nim,

            "nim_change_bps":
                -compression_bps,

            "stressed_nim_percent":
                round_value(
                    stressed_nim,
                    3
                ),

        },

        "calculations": {

            "estimated_eps_impact_percent":
                round_value(
                    -eps_impact_percent,
                    2
                ),

            "base_eps":
                base_eps,

            "stressed_eps":
                round_value(
                    stressed_eps,
                    3
                ),

            "estimated_eps_change":
                round_value(
                    stressed_eps - base_eps,
                    3
                ),

        },

        "provenance": {

            "source_system":
                "Synthetic Internal Pricing Engine",

            "source_type":
                "internal_api",

            "calculation_type":
                "scenario_analysis",

            "synthetic":
                True,

        },
    }


# ============================================================
# RELATIVE VALUATION RESPONSE
# ============================================================

def generate_peer_response(ticker):

    singapore_banks = [
        "D05",
        "O39",
        "U11",
    ]

    values = []

    for peer in singapore_banks:

        company = COMPANIES[peer]

        pe = (
            company["base_price"]
            /
            company["base_eps"]
        )

        pb = (
            company["base_price"]
            /
            company["base_book_value"]
        )

        values.append(
            {
                "ticker": peer,
                "company": company["name"],
                "pe": round_value(pe, 2),
                "pb": round_value(pb, 2),
                "roe": company["base_roe"],
            }
        )

    target = next(
        x
        for x in values
        if x["ticker"] == ticker
    )

    average_pe = sum(
        x["pe"]
        for x in values
    ) / len(values)

    average_pb = sum(
        x["pb"]
        for x in values
    ) / len(values)

    return {

        "api_response_type":
            "peer_valuation",

        "api_version":
            "1.0",

        "request_id":
            f"REQ-PEER-{ticker}-001",

        "generated_at":
            datetime.utcnow().isoformat() + "Z",

        "target_company":
            target,

        "peer_set":
            values,

        "peer_average": {

            "pe":
                round_value(
                    average_pe,
                    2
                ),

            "pb":
                round_value(
                    average_pb,
                    2
                ),

        },

        "relative_metrics": {

            "pe_premium_vs_peer":
                round_value(
                    (
                        target["pe"]
                        /
                        average_pe
                        - 1
                    )
                    * 100,
                    2
                ),

            "pb_premium_vs_peer":
                round_value(
                    (
                        target["pb"]
                        /
                        average_pb
                        - 1
                    )
                    * 100,
                    2
                ),

        },

        "provenance": {

            "source_system":
                "Synthetic Internal Pricing Engine",

            "source_type":
                "internal_api",

            "calculation_type":
                "relative_valuation",

            "synthetic":
                True,

        },
    }


# ============================================================
# WRITE RESPONSE
# ============================================================

def write_response(
    ticker,
    response,
    suffix,
):

    filename = (
        f"{ticker}_{suffix}.json"
    )

    output = OUTPUT_DIR / filename

    with open(
        output,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            response,
            f,
            indent=4,
        )

    print(
        f"Created: {output}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("GENERATING SYNTHETIC INTERNAL API RESPONSES")
    print("=" * 70)
    print()

    count = 0

    for ticker in COMPANIES:

        # --------------------------------------------
        # Valuation
        # --------------------------------------------

        valuation = (
            generate_valuation_response(
                ticker
            )
        )

        write_response(
            ticker,
            valuation,
            "valuation",
        )

        count += 1

        # --------------------------------------------
        # NIM stress
        # --------------------------------------------

        nim = (
            generate_nim_scenario_response(
                ticker
            )
        )

        write_response(
            ticker,
            nim,
            "nim_scenario",
        )

        count += 1

        # --------------------------------------------
        # Peer valuation
        # --------------------------------------------

        if ticker in [
            "D05",
            "O39",
            "U11",
        ]:

            peer = (
                generate_peer_response(
                    ticker
                )
            )

            write_response(
                ticker,
                peer,
                "peer_valuation",
            )

            count += 1

    print()
    print("=" * 70)
    print(
        f"Generated {count} synthetic API responses"
    )
    print("=" * 70)

    print()
    print(
        f"Output directory: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()