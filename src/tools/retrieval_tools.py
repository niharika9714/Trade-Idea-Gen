"""
Step 2D - Agent-facing retrieval tools.

This module intentionally exposes only the controlled registry.

The future agent should call:

    execute_retrieval_tool(name, arguments)

rather than importing SQL, file or API implementations directly.
"""

from typing import Any

from src.tools.tool_registry import (
    execute_tool,
    list_tools,
)


def execute_retrieval_tool(
    name: str,
    arguments: dict[str, Any],
) -> Any:
    """
    Execute one approved retrieval capability.
    """

    return execute_tool(
        name=name,
        arguments=arguments,
    )


def get_retrieval_tool_definitions() -> list[dict[str, Any]]:
    """
    Return tool definitions for future LLM function/tool calling.
    """

    return list_tools()