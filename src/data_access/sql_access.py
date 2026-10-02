"""
Native SQL market-data retrieval.

The LLM/agent should NOT receive the entire market database.

Instead:
    Agent -> SQL tool -> SQL database -> small result set

This keeps structured data retrieval precise and efficient.
"""

from __future__ import annotations

import sqlite3

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

MARKET_DB = (
    ROOT
    / "data"
    / "market_data"
    / "market.db"
)


# ============================================================
# CONNECTION
# ============================================================

def get_connection():

    if not MARKET_DB.is_file():

        raise FileNotFoundError(
            f"Market database not found: {MARKET_DB}"
        )

    connection = sqlite3.connect(
        MARKET_DB
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# TABLE INFORMATION
# ============================================================

def list_tables() -> list[str]:

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        return [
            row["name"]
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# TABLE SCHEMA
# ============================================================

def describe_table(
    table_name: str,
) -> list[dict[str, Any]]:

    allowed_tables = set(
        list_tables()
    )

    if table_name not in allowed_tables:

        raise ValueError(
            f"Unknown table: {table_name}"
        )

    connection = get_connection()

    try:

        rows = connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# GENERIC READ-ONLY QUERY
# ============================================================
def execute_query(sql, parameters=(), max_rows=500):
    """
    Execute a read-only SQL query and return rows as dictionaries.

    Only SELECT and WITH queries are allowed.
    """

    normalized_sql = sql.strip().lower()

    if not (
        normalized_sql.startswith("select")
        or normalized_sql.startswith("with")
    ):
        raise ValueError(
            "Only SELECT and WITH queries are allowed."
        )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(sql, parameters)

        columns = [
            description[0]
            for description in cursor.description
        ]

        raw_rows = cursor.fetchmany(max_rows)

        rows = [
            {
                column: value
                for column, value in zip(columns, row)
            }
            for row in raw_rows
        ]

        return {
            "rows": rows,
            "row_count": len(rows),
            "query": sql,
            "parameters": parameters,
            "provenance": {
                "source_system": "synthetic_market_database",
                "source_type": "sql",
                "retrieval_method": "direct_sql_query",
                "read_only": True,
            },
        }

    finally:
        conn.close()

# ============================================================
# CONVENIENCE: PRICE HISTORY
# ============================================================

def get_price_history(
    ticker: str,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 500,
    latest: bool = False,
) -> dict[str, Any]:

    sql = """
        SELECT
            ticker,
            trade_date,
            close_price,
            adjusted_close,
            daily_return
        FROM daily_prices
        WHERE ticker = ?
    """

    parameters = [ticker]

    if start_date:
        sql += """
            AND trade_date >= ?
        """
        parameters.append(start_date)

    if end_date:
        sql += """
            AND trade_date <= ?
        """
        parameters.append(end_date)

    if latest:
        sql += """
            ORDER BY trade_date DESC
            LIMIT ?
        """
    else:
        sql += """
            ORDER BY trade_date ASC
            LIMIT ?
        """

    parameters.append(limit)

    return execute_query(
        sql,
        tuple(parameters),
        max_rows=limit,
    )

# ============================================================
# CONVENIENCE: FUNDAMENTALS
# ============================================================

def get_fundamentals(
    ticker: str,
    limit: int = 20,
):
    """
    Return normalized fundamental records for a ticker.
    """

    sql = """
        SELECT *
        FROM fundamentals
        WHERE ticker = ?
        ORDER BY report_date DESC
        LIMIT ?
    """

    result = execute_query(
        sql,
        (
            ticker,
            limit,
        ),
        max_rows=limit,
    )

    return result["rows"]

# ============================================================
# CONVENIENCE: VOLUME
# ============================================================

def get_volume_history(
    ticker: str,
    limit: int = 100,
) -> dict[str, Any]:

    sql = """
        SELECT
            ticker,
            trade_date,
            volume,
            turnover
        FROM daily_volume
        WHERE ticker = ?
        ORDER BY trade_date DESC
        LIMIT ?
    """

    return execute_query(
        sql,
        (
            ticker,
            limit,
        ),
        max_rows=limit,
    )


# ============================================================
# CONVENIENCE: SECTOR PRICE
# ============================================================

def get_sector_history(
    sector: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:

    if sector:

        sql = """
            SELECT
                *
            FROM sector_prices
            WHERE sector = ?
            ORDER BY trade_date DESC
            LIMIT ?
        """

        return execute_query(
            sql,
            (
                sector,
                limit,
            ),
            max_rows=limit,
        )

    sql = """
        SELECT
            *
        FROM sector_prices
        ORDER BY trade_date DESC
        LIMIT ?
    """

    return execute_query(
        sql,
        (limit,),
        max_rows=limit,
    )