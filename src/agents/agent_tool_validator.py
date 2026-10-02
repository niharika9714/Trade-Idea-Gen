from __future__ import annotations

from typing import Any

from src.agents.agent_action import AgentAction


class AgentToolValidator:

    """
    Deterministic safety boundary.

    This validator does NOT decide which tool should be used.

    It only verifies that Qwen requested a registered tool and that
    the basic argument contract is satisfied.
    """

    def __init__(
        self,
        tool_definitions: list[dict[str, Any]],
    ) -> None:

        self.tool_definitions = {
            tool["name"]: tool
            for tool in tool_definitions
        }

    def validate(
        self,
        action: AgentAction,
    ) -> AgentAction:

        if action.is_finish:
            return action

        if not action.is_tool_call:
            raise ValueError(
                f"Unsupported action: {action.action}"
            )

        tool_name = action.tool_name

        if tool_name not in self.tool_definitions:
            raise ValueError(
                f"Agent requested unregistered tool: "
                f"{tool_name}"
            )

        if not isinstance(
            action.arguments,
            dict,
        ):
            raise ValueError(
                f"Arguments for '{tool_name}' "
                f"must be a dictionary"
            )

        tool = self.tool_definitions[
            tool_name
        ]

        parameters = tool.get(
            "parameters",
            {},
        )

        required = parameters.get(
            "required",
            [],
        )

        missing = [
            field
            for field in required
            if field not in action.arguments
        ]

        if missing:
            raise ValueError(
                f"Tool '{tool_name}' is missing "
                f"required arguments: {missing}"
            )

        return action