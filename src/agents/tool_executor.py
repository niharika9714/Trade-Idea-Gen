from typing import Any

from src.agents.tool_call_contract import (
    ToolCall,
    ToolExecutionResult,
)

from src.tools.retrieval_tools import (
    execute_retrieval_tool,
    get_retrieval_tool_definitions,
)


class AgentToolExecutor:
    """
    Security and validation boundary between the LLM
    and the actual retrieval tools.
    """

    def __init__(
        self,
        max_tool_calls: int = 20,
    ):

        if max_tool_calls < 1:
            raise ValueError(
                "max_tool_calls must be >= 1"
            )

        self.max_tool_calls = max_tool_calls

        self.executed_calls = 0

        self.tool_definitions = (
            get_retrieval_tool_definitions()
        )

        self.allowed_tools = {
            tool["name"]
            for tool in self.tool_definitions
        }

    def validate_tool_call(
        self,
        tool_call: ToolCall,
    ):

        if (
            tool_call.tool_name
            not in self.allowed_tools
        ):
            raise ValueError(
                "LLM attempted to execute "
                f"unregistered tool: "
                f"{tool_call.tool_name}"
            )

        if not isinstance(
            tool_call.arguments,
            dict,
        ):
            raise TypeError(
                "Tool arguments must be a dictionary."
            )

        return True

    def execute(
        self,
        tool_call: ToolCall,
    ) -> ToolExecutionResult:

        self.validate_tool_call(
            tool_call
        )

        if (
            self.executed_calls
            >= self.max_tool_calls
        ):
            raise RuntimeError(
                "Maximum tool-call limit exceeded."
            )

        self.executed_calls += 1

        try:

            result = execute_retrieval_tool(
                name=tool_call.tool_name,
                arguments=tool_call.arguments,
            )

            evidence_ids = []
            citations = []

            # Retrieval tools normally return an
            # EvidenceBundle.
            if hasattr(
                result,
                "ids",
            ):
                evidence_ids = result.ids()

            if hasattr(
                result,
                "citations",
            ):
                citations = result.citations()

            return ToolExecutionResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                success=True,
                result=result,
                evidence_ids=evidence_ids,
                citations=citations,
            )

        except Exception as exc:

            return ToolExecutionResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                error=str(exc),
            )