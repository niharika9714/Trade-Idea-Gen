from __future__ import annotations

from typing import Any

from src.agents.agent_action import AgentAction
from src.agents.agent_tool_validator import AgentToolValidator
from src.tools.retrieval_tools import execute_retrieval_tool


class AgentToolRuntime:

    def __init__(
        self,
        tool_definitions: list[dict[str, Any]],
    ) -> None:

        self.validator = AgentToolValidator(
            tool_definitions=tool_definitions
        )

    def execute(
        self,
        action: AgentAction,
    ) -> dict[str, Any]:

        action = self.validator.validate(
            action
        )

        if action.is_finish:

            return {
                "success": True,
                "action": "finish",
                "tool_name": None,
                "arguments": {},
                "result": None,
                "raw_result": None,
            }

        try:

            raw_result = execute_retrieval_tool(
                name=action.tool_name,
                arguments=action.arguments,
            )

            if hasattr(
                raw_result,
                "to_dict",
            ):
                result_for_llm = (
                    raw_result.to_dict()
                )
            else:
                result_for_llm = raw_result

            return {
                "success": True,
                "action": "tool_call",
                "tool_name": action.tool_name,
                "arguments": action.arguments,
                "result": result_for_llm,

                # IMPORTANT:
                # Keep the actual object so the orchestrator
                # can preserve EvidenceBundle/provenance.
                "raw_result": raw_result,
            }

        except Exception as exc:

            return {
                "success": False,
                "action": "tool_call",
                "tool_name": action.tool_name,
                "arguments": action.arguments,
                "error": str(exc),
                "raw_result": None,
            }