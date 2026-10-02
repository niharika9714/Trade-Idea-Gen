from __future__ import annotations

from typing import Any


def to_ollama_tool(
    tool_definition: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert our internal ToolRegistry definition into the
    Ollama tool-calling schema.
    """

    required_fields = tool_definition.get(
        "parameters",
        {},
    ).get(
        "required",
        [],
    )

    properties = tool_definition.get(
        "parameters",
        {},
    ).get(
        "properties",
        {},
    )

    return {
        "type": "function",
        "function": {
            "name": tool_definition["name"],
            "description": tool_definition["description"],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_fields,
            },
        },
    }


def to_ollama_tools(
    tool_definitions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert all registered retrieval tools.
    """

    return [
        to_ollama_tool(tool)
        for tool in tool_definitions
    ]