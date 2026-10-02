"""
Native access to synthetic internal API responses.

In production this layer can later be replaced by an HTTP/API
connector without changing the agent's logical tool interface.
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

API_DIR = (
    ROOT
    / "data"
    / "internal_api"
    / "responses"
)


# ============================================================
# LIST RESPONSES
# ============================================================

def list_api_responses() -> list[str]:

    if not API_DIR.exists():

        return []

    return sorted(
        path.name
        for path in API_DIR.glob(
            "*.json"
        )
    )


# ============================================================
# GET RESPONSE
# ============================================================

def get_api_response(
    filename: str,
) -> dict[str, Any]:

    path = API_DIR / filename

    if not path.is_file():

        raise FileNotFoundError(
            f"API response not found: {filename}"
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return {
        "response": data,

        "source": {
            "source_path": str(
                path.relative_to(ROOT)
            ).replace("\\", "/"),

            "filename": path.name,
        },

        "provenance": {
            "retrieval_method": "internal_api_response",

            "source_system": (
                data.get(
                    "provenance",
                    {}
                ).get(
                    "source_system",
                    "synthetic_internal_api",
                )
            ),

            "synthetic": True,
        },
    }


# ============================================================
# FIND API RESPONSES
# ============================================================

def find_api_responses(
    ticker: str | None = None,
    response_type: str | None = None,
) -> list[dict[str, Any]]:

    results = []

    for filename in list_api_responses():

        name = filename.lower()

        if ticker:

            if ticker.lower() not in name:

                continue

        if response_type:

            if response_type.lower() not in name:

                continue

        results.append(
            {
                "filename": filename,

                "ticker": ticker,

                "response_type": response_type,

                "source_path": (
                    "data/internal_api/"
                    f"responses/{filename}"
                ),
            }
        )

    return results