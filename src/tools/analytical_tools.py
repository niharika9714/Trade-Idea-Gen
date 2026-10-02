from __future__ import annotations

from typing import Any

from src.data_access.sql_access import (get_price_history, execute_query)
from src.provenance.evidence import Evidence, EvidenceBundle


def _normalise_rows(
    ticker: str,
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]]:

    result = get_price_history(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        limit=5000,
    )

    return result["rows"]


def _build_calculation_evidence(
    ticker: str,
    start_date: str,
    end_date: str,
    metric: str,
    value: float,
    start_price: float,
    end_price: float,
    start_locator: str,
    end_locator: str,
) -> EvidenceBundle:
    """
    Build deterministic calculation evidence with source,
    instrument, currency, date-range and calculation provenance.
    """

    instrument_result = execute_query(
        """
        SELECT
            instrument_id,
            ticker,
            instrument_type,
            exchange,
            currency
        FROM instruments
        WHERE ticker = ?
        """,
        (ticker,),
        max_rows=1,
    )

    instrument_rows = instrument_result["rows"]

    if not instrument_rows:
        raise ValueError(
            f"No instrument metadata found for ticker: {ticker}"
        )

    instrument = instrument_rows[0]

    if metric == "price_change":

        calculation = (
            f"{end_price} - {start_price}"
        )

    elif metric == "return":

        calculation = (
            f"({end_price} - {start_price}) / "
            f"{start_price}"
        )

    else:

        raise ValueError(
            f"Unsupported calculation metric: {metric}"
        )

    input_citations = [
        start_locator,
        end_locator,
    ]

    locator = (
        f"daily_prices.{metric}"
        f"?ticker={ticker}"
        f"&start_date={start_date}"
        f"&end_date={end_date}"
    )
    actual_start_date = (
        start_locator.split("trade_date=")[-1]
    )

    actual_end_date = (
        end_locator.split("trade_date=")[-1]
    )

    content = {
        "ticker": ticker,
        "metric": metric,

        "requested_start_date": start_date,
        "requested_end_date": end_date,
        "actual_start_date": actual_start_date,
        "actual_end_date": actual_end_date,

        "start_price": start_price,
        "end_price": end_price,

        "value": value,

        "currency": instrument["currency"],
        "exchange": instrument["exchange"],
        "instrument_type": instrument["instrument_type"],
        "instrument_id": instrument["instrument_id"],

        "calculation": calculation,

        "input_citations": input_citations,
    }

    metadata = {
        "calculation_type": metric,

        "input_citations": input_citations,

        "requested_date_range": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "actual_date_range": {
            "start_date": actual_start_date,
            "end_date": actual_end_date,
        },

        "currency": instrument["currency"],
        "exchange": instrument["exchange"],

        "instrument_id": instrument["instrument_id"],
    }

    provenance = {
        "source_system": "synthetic_market_database",
        "retrieval_method": "deterministic_calculation",
        "calculation_engine": "python",

        "source_type": "calculation",
        "source": "market.db",
        "locator": locator,
        "content_type": "derived_metric",

        "synthetic": True,

        "input_citations": input_citations,

        "currency_source": (
            "market.db#instruments.currency"
        ),

        "instrument_source": (
            "market.db#instruments"
        ),
    }

    evidence = Evidence(
        source_type="calculation",
        source="market.db",
        locator=locator,
        content_type="derived_metric",

        content=content,

        ticker=ticker,
        event_id=None,

        source_system="synthetic_market_database",

        synthetic=True,

        metadata=metadata,

        provenance=provenance,
    )

    return EvidenceBundle(
        [evidence]
    )


def calculate_price_change(
    ticker: str,
    start_date: str,
    end_date: str,
) -> EvidenceBundle:
    """
    Calculate the absolute share-price change over a period.

    Use this when the user asks how much a share price
    moved between two dates.

    The calculation is deterministic Python logic.
    The LLM must not calculate the result itself.
    """

    rows = _normalise_rows(
        ticker,
        start_date,
        end_date,
    )

    if not rows:
        return EvidenceBundle()

    first = rows[0]
    last = rows[-1]

    start_price = float(
        first["close_price"]
    )

    end_price = float(
        last["close_price"]
    )

    change = (
        end_price
        - start_price
    )

    start_locator = (
        "market.db#daily_prices."
        f"trade_date={first['trade_date']}"
    )

    end_locator = (
        "market.db#daily_prices."
        f"trade_date={last['trade_date']}"
    )

    return _build_calculation_evidence(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        metric="price_change",
        value=change,
        start_price=start_price,
        end_price=end_price,
        start_locator=start_locator,
        end_locator=end_locator,
    )


def calculate_return(
    ticker: str,
    start_date: str,
    end_date: str,
) -> EvidenceBundle:
    """
    Calculate percentage return over a period.

    Return is:

        (end_price - start_price) / start_price

    The calculation is deterministic Python logic.
    The LLM must not calculate the result itself.
    """

    rows = _normalise_rows(
        ticker,
        start_date,
        end_date,
    )

    if not rows:
        return EvidenceBundle()

    first = rows[0]
    last = rows[-1]

    start_price = float(
        first["close_price"]
    )

    end_price = float(
        last["close_price"]
    )

    if start_price == 0:
        raise ValueError(
            "Cannot calculate return from a zero start price."
        )

    result = (
        end_price - start_price
    ) / start_price

    start_locator = (
        "market.db#daily_prices."
        f"trade_date={first['trade_date']}"
    )

    end_locator = (
        "market.db#daily_prices."
        f"trade_date={last['trade_date']}"
    )

    evidence = _build_calculation_evidence(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        metric="return",
        value=result,
        start_price=start_price,
        end_price=end_price,
        start_locator=start_locator,
        end_locator=end_locator,
    )

    return evidence