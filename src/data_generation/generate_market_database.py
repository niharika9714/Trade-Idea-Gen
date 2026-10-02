from pathlib import Path
import sqlite3
import random
import math
from datetime import date, timedelta

import numpy as np


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "market_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "market.db"

START_DATE = date(2022, 1, 3)
END_DATE = date(2026, 9, 25)

random.seed(42)
np.random.seed(42)


# ============================================================
# Synthetic instruments
# ============================================================

INSTRUMENTS = [
    {
        "ticker": "D05",
        "company": "DBS Group",
        "sector": "Singapore Banks",
        "currency": "SGD",
        "base_price": 30.0,
        "volatility": 0.018,
        "beta": 1.00
    },
    {
        "ticker": "O39",
        "company": "OCBC",
        "sector": "Singapore Banks",
        "currency": "SGD",
        "base_price": 12.0,
        "volatility": 0.015,
        "beta": 0.85
    },
    {
        "ticker": "U11",
        "company": "UOB",
        "sector": "Singapore Banks",
        "currency": "SGD",
        "base_price": 28.0,
        "volatility": 0.016,
        "beta": 0.90
    },
    {
        "ticker": "HSBA",
        "company": "HSBC",
        "sector": "Global Banks",
        "currency": "GBP",
        "base_price": 5.50,
        "volatility": 0.017,
        "beta": 1.05
    },
    {
        "ticker": "STAN",
        "company": "Standard Chartered",
        "sector": "Global Banks",
        "currency": "GBP",
        "base_price": 7.00,
        "volatility": 0.020,
        "beta": 1.15
    }
]


# ============================================================
# Synthetic event dates
#
# These deliberately line up with events.py so the agent can
# later correlate market movements with research documents.
# ============================================================

EVENTS = {
    "D05": {
        date(2024, 2, 15): -0.035,
        date(2024, 5, 10): 0.028,
        date(2024, 8, 8): -0.018,
        date(2024, 11, 7): 0.032,
        date(2025, 2, 14): 0.045,
        date(2025, 5, 9): -0.022,
        date(2025, 8, 8): 0.018,
        date(2025, 11, 6): -0.040,
        date(2026, 2, 13): -0.042,
    },
    "O39": {
        date(2024, 2, 15): -0.020,
        date(2024, 5, 10): 0.015,
        date(2024, 8, 8): -0.010,
        date(2024, 11, 7): 0.022,
        date(2025, 2, 14): 0.030,
        date(2025, 5, 9): -0.012,
        date(2025, 8, 8): 0.012,
        date(2025, 11, 6): -0.025,
        date(2026, 2, 13): -0.025,
    },
    "U11": {
        date(2024, 2, 15): -0.018,
        date(2024, 5, 10): 0.012,
        date(2024, 8, 8): -0.008,
        date(2024, 11, 7): 0.018,
        date(2025, 2, 14): 0.025,
        date(2025, 5, 9): -0.010,
        date(2025, 8, 8): 0.010,
        date(2025, 11, 6): -0.020,
        date(2026, 2, 13): -0.021,
    },
    "HSBA": {
        date(2024, 2, 20): 0.015,
        date(2025, 2, 18): 0.020,
        date(2026, 2, 17): -0.018,
    },
    "STAN": {
        date(2024, 2, 20): 0.010,
        date(2025, 2, 18): 0.015,
        date(2026, 2, 17): -0.022,
    }
}


# ============================================================
# Database setup
# ============================================================

def create_database():

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    # --------------------------------------------------------
    # Companies
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE companies (
            company_id TEXT PRIMARY KEY,
            ticker TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            sector TEXT NOT NULL,
            currency TEXT NOT NULL,
            synthetic INTEGER NOT NULL
        )
    """)

    # --------------------------------------------------------
    # Instruments
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE instruments (
            instrument_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            instrument_type TEXT NOT NULL,
            exchange TEXT NOT NULL,
            currency TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # Daily prices
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE daily_prices (
            price_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date DATE NOT NULL,
            ticker TEXT NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            adjusted_close REAL NOT NULL,
            previous_close REAL,
            daily_return REAL,
            FOREIGN KEY (ticker) REFERENCES instruments(ticker)
        )
    """)

    # --------------------------------------------------------
    # Daily volume
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE daily_volume (
            volume_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date DATE NOT NULL,
            ticker TEXT NOT NULL,
            volume INTEGER NOT NULL,
            turnover REAL NOT NULL,
            FOREIGN KEY (ticker) REFERENCES instruments(ticker)
        )
    """)

    # --------------------------------------------------------
    # Fundamentals
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE fundamentals (
            fundamental_id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date DATE NOT NULL,
            ticker TEXT NOT NULL,
            revenue REAL,
            net_interest_income REAL,
            net_interest_margin REAL,
            roe REAL,
            roa REAL,
            loan_growth REAL,
            deposit_growth REAL,
            cet1_ratio REAL,
            npl_ratio REAL,
            credit_cost REAL,
            cost_income_ratio REAL,
            eps REAL,
            book_value_per_share REAL,
            pe_ratio REAL,
            pb_ratio REAL
        )
    """)

    # --------------------------------------------------------
    # Dividends
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE dividends (
            dividend_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            ex_date DATE NOT NULL,
            dividend_per_share REAL NOT NULL,
            dividend_type TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # Sector index
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE sector_prices (
            trade_date DATE NOT NULL,
            sector TEXT NOT NULL,
            close_price REAL NOT NULL,
            daily_return REAL,
            PRIMARY KEY (trade_date, sector)
        )
    """)

    # --------------------------------------------------------
    # Useful indexes
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX idx_prices_ticker_date
        ON daily_prices(ticker, trade_date)
    """)

    cursor.execute("""
        CREATE INDEX idx_volume_ticker_date
        ON daily_volume(ticker, trade_date)
    """)

    cursor.execute("""
        CREATE INDEX idx_fundamentals_ticker_date
        ON fundamentals(ticker, report_date)
    """)

    conn.commit()

    return conn


# ============================================================
# Generate trading days
# ============================================================

def trading_days():

    current = START_DATE

    while current <= END_DATE:

        # Monday = 0
        # Friday = 4

        if current.weekday() < 5:
            yield current

        current += timedelta(days=1)


# ============================================================
# Generate company price history
# ============================================================

def generate_prices(conn):

    cursor = conn.cursor()

    days = list(trading_days())

    sector_return = {}

    for instrument in INSTRUMENTS:

        ticker = instrument["ticker"]

        price = instrument["base_price"]

        previous_close = None

        for trade_date in days:

            # Market/sector movement
            market_component = np.random.normal(
                0,
                0.006
            )

            idiosyncratic_component = np.random.normal(
                0,
                instrument["volatility"]
            )

            daily_return = (
                0.00012
                + instrument["beta"] * market_component
                + idiosyncratic_component
            )

            # ------------------------------------------------
            # Apply event shock
            # ------------------------------------------------

            event_shock = EVENTS.get(
                ticker,
                {}
            ).get(
                trade_date,
                0
            )

            daily_return += event_shock

            # ------------------------------------------------
            # Macro shock around Sep 2025
            # ------------------------------------------------

            if (
                date(2025, 9, 18)
                <= trade_date
                <= date(2025, 9, 22)
            ):
                daily_return -= 0.012

            # ------------------------------------------------
            # Keep prices realistic
            # ------------------------------------------------

            daily_return = max(
                -0.12,
                min(0.12, daily_return)
            )

            new_close = price * (
                1 + daily_return
            )

            # Intraday range
            intraday_volatility = abs(
                np.random.normal(
                    0.012,
                    0.006
                )
            )

            open_price = price * (
                1 + np.random.normal(
                    0,
                    0.003
                )
            )

            high_price = max(
                open_price,
                new_close
            ) * (
                1 + intraday_volatility
            )

            low_price = min(
                open_price,
                new_close
            ) * (
                1 - intraday_volatility
            )

            # ------------------------------------------------
            # Volume
            # ------------------------------------------------

            base_volume = {
                "D05": 4_000_000,
                "O39": 3_000_000,
                "U11": 2_500_000,
                "HSBA": 12_000_000,
                "STAN": 7_000_000
            }[ticker]

            volume_multiplier = np.random.lognormal(
                mean=0,
                sigma=0.35
            )

            # Earnings/event days produce volume spikes
            if trade_date in EVENTS.get(ticker, {}):
                volume_multiplier *= 3.5

            if (
                date(2025, 9, 18)
                <= trade_date
                <= date(2025, 9, 22)
            ):
                volume_multiplier *= 2.0

            volume = int(
                base_volume *
                volume_multiplier
            )

            turnover = (
                volume *
                new_close
            )

            # ------------------------------------------------
            # Insert price
            # ------------------------------------------------

            cursor.execute(
                """
                INSERT INTO daily_prices (
                    trade_date,
                    ticker,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    adjusted_close,
                    previous_close,
                    daily_return
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade_date.isoformat(),
                    ticker,
                    round(open_price, 4),
                    round(high_price, 4),
                    round(low_price, 4),
                    round(new_close, 4),
                    round(new_close, 4),
                    (
                        round(previous_close, 4)
                        if previous_close
                        else None
                    ),
                    round(daily_return, 6)
                )
            )

            cursor.execute(
                """
                INSERT INTO daily_volume (
                    trade_date,
                    ticker,
                    volume,
                    turnover
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    trade_date.isoformat(),
                    ticker,
                    volume,
                    round(turnover, 2)
                )
            )

            # Store sector return
            sector = instrument["sector"]

            if trade_date not in sector_return:
                sector_return[trade_date] = {}

            sector_return[trade_date].setdefault(
                sector,
                []
            )

            sector_return[
                trade_date
            ][sector].append(
                daily_return
            )

            price = new_close
            previous_close = new_close

    conn.commit()

    return sector_return


# ============================================================
# Generate sector indexes
# ============================================================

def generate_sector_prices(
    conn,
    sector_returns
):

    cursor = conn.cursor()

    sector_prices = {
        "Singapore Banks": 1000.0,
        "Global Banks": 1000.0
    }

    previous_values = {}

    for trade_date in sorted(
        sector_returns.keys()
    ):

        for sector, returns in sector_returns[
            trade_date
        ].items():

            avg_return = float(
                np.mean(returns)
            )

            sector_prices[sector] *= (
                1 + avg_return
            )

            previous = previous_values.get(
                sector
            )

            cursor.execute(
                """
                INSERT INTO sector_prices (
                    trade_date,
                    sector,
                    close_price,
                    daily_return
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    trade_date.isoformat(),
                    sector,
                    round(
                        sector_prices[sector],
                        4
                    ),
                    (
                        round(avg_return, 6)
                        if previous is not None
                        else None
                    )
                )
            )

            previous_values[sector] = (
                sector_prices[sector]
            )

    conn.commit()


# ============================================================
# Generate fundamentals
# ============================================================

def generate_fundamentals(conn):

    cursor = conn.cursor()

    report_dates = [
        date(2024, 2, 15),
        date(2024, 5, 10),
        date(2024, 8, 8),
        date(2024, 11, 7),
        date(2025, 2, 14),
        date(2025, 5, 9),
        date(2025, 8, 8),
        date(2025, 11, 6),
        date(2026, 2, 13)
    ]

    base_values = {

        "D05": {
            "revenue": 18000,
            "nii": 10500,
            "nim": 2.25,
            "roe": 14.5,
            "roa": 1.35,
            "loan_growth": 5.5,
            "deposit_growth": 4.5,
            "cet1": 17.2,
            "npl": 1.1,
            "credit_cost": 15,
            "cost_income": 40,
            "eps": 3.25,
            "bvps": 24.0
        },

        "O39": {
            "revenue": 14500,
            "nii": 8500,
            "nim": 2.15,
            "roe": 13.0,
            "roa": 1.20,
            "loan_growth": 4.5,
            "deposit_growth": 4.0,
            "cet1": 15.8,
            "npl": 1.2,
            "credit_cost": 18,
            "cost_income": 42,
            "eps": 1.35,
            "bvps": 11.5
        },

        "U11": {
            "revenue": 12500,
            "nii": 7600,
            "nim": 2.05,
            "roe": 12.5,
            "roa": 1.15,
            "loan_growth": 4.0,
            "deposit_growth": 3.5,
            "cet1": 16.0,
            "npl": 1.3,
            "credit_cost": 20,
            "cost_income": 43,
            "eps": 2.80,
            "bvps": 22.0
        },

        "HSBA": {
            "revenue": 62000,
            "nii": 35000,
            "nim": 1.70,
            "roe": 11.5,
            "roa": 0.75,
            "loan_growth": 3.5,
            "deposit_growth": 3.0,
            "cet1": 14.5,
            "npl": 2.0,
            "credit_cost": 28,
            "cost_income": 55,
            "eps": 0.95,
            "bvps": 5.80
        },

        "STAN": {
            "revenue": 18000,
            "nii": 9500,
            "nim": 1.65,
            "roe": 10.0,
            "roa": 0.65,
            "loan_growth": 3.0,
            "deposit_growth": 2.5,
            "cet1": 14.0,
            "npl": 2.2,
            "credit_cost": 35,
            "cost_income": 58,
            "eps": 0.72,
            "bvps": 6.20
        }
    }

    for report_index, report_date in enumerate(
        report_dates
    ):

        for instrument in INSTRUMENTS:

            ticker = instrument["ticker"]

            base = base_values[ticker]

            trend = (
                report_index * 0.015
            )

            noise = np.random.normal(
                0,
                0.02
            )

            revenue = base["revenue"] * (
                1 + trend + noise
            )

            nii = base["nii"] * (
                1 + trend + noise
            )

            nim = base["nim"] + np.random.normal(
                0,
                0.05
            )

            roe = base["roe"] + np.random.normal(
                0,
                0.25
            )

            roa = base["roa"] + np.random.normal(
                0,
                0.03
            )

            loan_growth = (
                base["loan_growth"]
                + np.random.normal(0, 0.5)
            )

            deposit_growth = (
                base["deposit_growth"]
                + np.random.normal(0, 0.5)
            )

            cet1 = (
                base["cet1"]
                + np.random.normal(0, 0.15)
            )

            npl = max(
                0.5,
                base["npl"]
                + np.random.normal(0, 0.05)
            )

            credit_cost = max(
                5,
                base["credit_cost"]
                + np.random.normal(0, 3)
            )

            cost_income = (
                base["cost_income"]
                + np.random.normal(0, 0.8)
            )

            eps = base["eps"] * (
                1 + trend + noise
            )

            bvps = base["bvps"] * (
                1 + trend * 0.5
            )

            # P/E and P/B will be based on
            # approximate synthetic market values.
            pe = (
                10
                + np.random.normal(0, 0.5)
            )

            pb = (
                1.3
                + np.random.normal(0, 0.08)
            )

            cursor.execute(
                """
                INSERT INTO fundamentals (
                    report_date,
                    ticker,
                    revenue,
                    net_interest_income,
                    net_interest_margin,
                    roe,
                    roa,
                    loan_growth,
                    deposit_growth,
                    cet1_ratio,
                    npl_ratio,
                    credit_cost,
                    cost_income_ratio,
                    eps,
                    book_value_per_share,
                    pe_ratio,
                    pb_ratio
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_date.isoformat(),
                    ticker,
                    round(revenue, 2),
                    round(nii, 2),
                    round(nim, 3),
                    round(roe, 3),
                    round(roa, 3),
                    round(loan_growth, 3),
                    round(deposit_growth, 3),
                    round(cet1, 3),
                    round(npl, 3),
                    round(credit_cost, 3),
                    round(cost_income, 3),
                    round(eps, 3),
                    round(bvps, 3),
                    round(pe, 3),
                    round(pb, 3)
                )
            )

    conn.commit()


# ============================================================
# Generate dividends
# ============================================================

def generate_dividends(conn):

    cursor = conn.cursor()

    dividend_data = {
        "D05": 0.55,
        "O39": 0.42,
        "U11": 0.60,
        "HSBA": 0.25,
        "STAN": 0.18
    }

    for instrument in INSTRUMENTS:

        ticker = instrument["ticker"]

        base_dividend = dividend_data[ticker]

        for year in [2023, 2024, 2025, 2026]:

            for month in [5, 11]:

                ex_date = date(
                    year,
                    month,
                    15
                )

                dividend = (
                    base_dividend
                    * (1 + 0.04 * (year - 2023))
                )

                cursor.execute(
                    """
                    INSERT INTO dividends (
                        ticker,
                        ex_date,
                        dividend_per_share,
                        dividend_type
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        ticker,
                        ex_date.isoformat(),
                        round(dividend, 4),
                        "ORDINARY"
                    )
                )

    conn.commit()


# ============================================================
# Main
# ============================================================

def main():

    print("\nCreating synthetic market database...\n")

    conn = create_database()

    # Companies
    cursor = conn.cursor()

    for index, instrument in enumerate(
        INSTRUMENTS,
        start=1
    ):

        cursor.execute(
            """
            INSERT INTO companies (
                company_id,
                ticker,
                company_name,
                sector,
                currency,
                synthetic
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                f"COMP-{index:03d}",
                instrument["ticker"],
                instrument["company"],
                instrument["sector"],
                instrument["currency"],
                1
            )
        )

        exchange = (
            "SGX"
            if instrument["currency"] == "SGD"
            else "LSE"
        )

        cursor.execute(
            """
            INSERT INTO instruments (
                instrument_id,
                ticker,
                instrument_type,
                exchange,
                currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                f"INST-{index:03d}",
                instrument["ticker"],
                "EQUITY",
                exchange,
                instrument["currency"]
            )
        )

    conn.commit()

    # Generate data
    sector_returns = generate_prices(conn)

    generate_sector_prices(
        conn,
        sector_returns
    )

    generate_fundamentals(conn)

    generate_dividends(conn)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    cursor = conn.cursor()

    tables = [
        "companies",
        "instruments",
        "daily_prices",
        "daily_volume",
        "fundamentals",
        "dividends",
        "sector_prices"
    ]

    print("\nDatabase generated successfully.\n")

    for table in tables:

        cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        )

        count = cursor.fetchone()[0]

        print(
            f"{table:20} {count:,} rows"
        )

    conn.close()

    print(
        f"\nDatabase location:\n{DB_PATH}\n"
    )


if __name__ == "__main__":
    main()