"""
Step 2D - Agent Tool Registry

Defines the controlled set of retrieval capabilities exposed
to the future agent.

The registry is deliberately separate from the implementation.

Agent:
    "What tools do I have?"

Registry:
    "These are the tools."

Tool implementation:
    "Here is how each tool actually retrieves evidence."
"""

from typing import Any, Callable

from src.data_access.retrieval_service import (
    search_documents,
    get_document,
    search_news,
    get_prices,
    get_fundamental_data,
    get_volume,
    run_sql,
    get_internal_api,
    discover_sources,
)
from src.tools.analytical_tools import (
    calculate_price_change,
    calculate_return,
)

# ---------------------------------------------------------------------------
# Tool specification
# ---------------------------------------------------------------------------

class ToolSpec:
    """
    Lightweight tool definition.

    This will later be convertible into:
        - OpenAI tool schema
        - Anthropic tool schema
        - MCP tool schema
        - internal agent framework schema
    """

    def __init__(
        self,
        name: str,
        description: str,
        function: Callable[..., Any],
        parameters: dict[str, Any],
    ):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = {

    "search_documents": ToolSpec(
        name="search_documents",
        description=(
            "Search PDF, PPTX, DOCX and MSG research documents "
            "using deterministic lexical matching. Returns "
            "layout-aware Evidence with document-level provenance."
        ),
        function=search_documents,
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Terms to search for.",
                },
                "ticker": {
                    "type": "string",
                    "description": "Optional company ticker.",
                },
                "event_id": {
                    "type": "string",
                    "description": "Optional event identifier.",
                },
                "extension": {
                    "type": "string",
                    "description": (
                        "Optional file extension such as "
                        ".pdf, .pptx, .docx or .msg."
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum source documents.",
                },
            },
            "required": ["query"],
        },
    ),

    "get_document": ToolSpec(
        name="get_document",
        description=(
            "Retrieve a complete document as layout-aware "
            "Evidence."
        ),
        function=get_document,
        parameters={
            "type": "object",
            "properties": {
                "source_path": {
                    "type": "string",
                    "description": "Document source path.",
                },
            },
            "required": ["source_path"],
        },
    ),

    "search_news": ToolSpec(
        name="search_news",
        description=(
            "Search stored financial news articles and return "
            "article-level Evidence with source provenance."
        ),
        function=search_news,
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "News search terms.",
                },
                "ticker": {
                    "type": "string",
                    "description": "Optional ticker.",
                },
                "event_id": {
                    "type": "string",
                    "description": "Optional event identifier.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum articles.",
                },
            },
            "required": [],
        },
    ),

    "get_prices": ToolSpec(
        name="get_prices",
        description=(
            "Retrieve historical daily market prices directly "
            "from the market database."
        ),
        function=get_prices,
        parameters={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                },
                "start_date": {
                    "type": "string",
                },
                "end_date": {
                    "type": "string",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of price records to retrieve."
                },
                "latest": {
                    "type": "boolean",
                    "description": "Return only the latest available price record."
                },
            },
            "required": ["ticker"],
        },
    ),

    "get_fundamental_data": ToolSpec(
        name="get_fundamental_data",
        description=(
            "Retrieve company fundamental data directly "
            "from the market database."
        ),
        function=get_fundamental_data,
        parameters={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                },
                "limit": {
                    "type": "integer",
                },
            },
            "required": ["ticker"],
        },
    ),

    "get_volume": ToolSpec(
        name="get_volume",
        description=(
            "Retrieve historical trading volume directly "
            "from the market database."
        ),
        function=get_volume,
        parameters={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                },
                "limit": {
                    "type": "integer",
                },
            },
            "required": ["ticker"],
        },
    ),

    "run_sql": ToolSpec(
        name="run_sql",
        description=(
            "Execute a read-only SELECT or WITH SQL query against "
            "the market database and return the result as Evidence. "
            "Use this for analytical calculations that cannot be "
            "expressed by the standard market-data tools."
        ),
        function=run_sql,
        parameters={
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": (
                        "Read-only SELECT or WITH SQL statement."
                    ),
                },
                "parameters": {
                    "type": "array",
                    "description": "Parameterized SQL values.",
                },
                "ticker": {
                    "type": "string",
                },
                "table_name": {
                    "type": "string",
                },
                "locator_field": {
                    "type": "string",
                },
                "max_rows": {
                    "type": "integer",
                },
            },
            "required": ["sql"],
        },
    ),

    "get_internal_api": ToolSpec(
        name="get_internal_api",
        description=(
            "Retrieve synthetic internal pricing-engine responses "
            "and return them as Evidence."
        ),
        function=get_internal_api,
        parameters={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                },
                "response_type": {
                    "type": "string",
                },
            },
            "required": [],
        },
    ),

        "discover_sources": ToolSpec(
            name="discover_sources",
            description=(
                "Discover candidate source files without reading "
                "their contents."
            ),
            function=discover_sources,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                    },
                    "ticker": {
                        "type": "string",
                    },
                    "event_id": {
                        "type": "string",
                    },
                    "extension": {
                        "type": "string",
                    },
                    "max_results": {
                        "type": "integer",
                    },
                },
                "required": ["query"],
            },
        ),
    
        "calculate_price_change": ToolSpec(
            name="calculate_price_change",
            description=(
                "Deterministically calculate the absolute share-price "
                "change between two dates for a ticker. Use when the "
                "user asks how much a share price moved, increased, "
                "or decreased over a period. The calculation is "
                "performed by Python from structured market data."
            ),
            function=calculate_price_change,
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Ticker symbol.",
                    },
                    "start_date": {
                        "type": "string",
                        "description": (
                            "Start date in YYYY-MM-DD format."
                        ),
                    },
                    "end_date": {
                        "type": "string",
                        "description": (
                            "End date in YYYY-MM-DD format."
                        ),
                    },
                },
                "required": [
                    "ticker",
                    "start_date",
                    "end_date",
                ],
            },
        ),
    
        "calculate_return": ToolSpec(
            name="calculate_return",
            description=(
                "Deterministically calculate percentage return between "
                "two dates for a ticker. Use when the user asks for "
                "return or performance over a period. The calculation "
                "is performed by Python from structured market data."
            ),
            function=calculate_return,
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Ticker symbol.",
                    },
                    "start_date": {
                        "type": "string",
                        "description": (
                            "Start date in YYYY-MM-DD format."
                        ),
                    },
                    "end_date": {
                        "type": "string",
                        "description": (
                            "End date in YYYY-MM-DD format."
                        ),
                    },
                },
                "required": [
                    "ticker",
                    "start_date",
                    "end_date",
                ],
            },
        ),
    }


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def get_tool(
    name: str,
) -> ToolSpec:
    """Return one registered tool."""

    if name not in TOOLS:
        raise KeyError(
            f"Unknown retrieval tool: {name}"
        )

    return TOOLS[name]


def list_tools() -> list[dict[str, Any]]:
    """Return all registered tool definitions."""

    return [
        tool.to_dict()
        for tool in TOOLS.values()
    ]


def execute_tool(
    name: str,
    arguments: dict[str, Any],
) -> Any:
    """
    Execute a registered tool.

    This is the only function the future agent needs
    to use for tool invocation.
    """

    tool = get_tool(name)

    return tool.function(**arguments)