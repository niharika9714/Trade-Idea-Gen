from abc import ABC, abstractmethod
from ast import arguments
from ast import arguments
from typing import Any

from pandas import date_range

from src.agents.agent_contract import AgentDecision
from src.agents.tool_call_contract import ToolCall


class LLMAdapter(ABC):
    """
    Provider-independent LLM interface.

    Step 3A:
        generate_agent_decision()

    Step 3B:
        generate_tool_calls()
    """

    @abstractmethod
    def generate_agent_decision(
        self,
        query: str,
        query_intent: Any,
        available_tools: list[dict[str, Any]],
    ) -> AgentDecision:
        raise NotImplementedError

    @abstractmethod
    def generate_tool_calls(
        self,
        query: str,
        agent_decision: AgentDecision,
        previous_tool_results: list[
            dict[str, Any]
        ],
    ) -> list[ToolCall]:
        raise NotImplementedError


class MockLLMAdapter(LLMAdapter):
    """
    Deterministic mock LLM.

    This allows us to test the agentic architecture
    without an API key or external model.
    """

    def generate_agent_decision(
        self,
        query: str,
        query_intent: Any,
        available_tools: list[dict[str, Any]],
    ) -> AgentDecision:

        if not query.strip():
            raise ValueError(
                "query must be a non-empty string"
            )

        intents = list(
            getattr(
                query_intent,
                "intents",
                [],
            )
        )

        tickers = list(
            getattr(
                query_intent,
                "tickers",
                [],
            )
        )

        requested_sources = list(
            getattr(
                query_intent,
                "requested_sources",
                [],
            )
        )

        tool_names = {
            tool["name"]
            for tool in available_tools
        }

        intent_tool_map = {
            "price": "get_prices",
            "fundamentals": "get_fundamental_data",
            "volume": "get_volume",
            "news": "search_news",
            "research_report": "search_documents",
            "valuation": "get_internal_api",
        }

        selected_tools = []

        for intent in intents:

            tool_name = intent_tool_map.get(
                intent
            )

            if (
                tool_name
                and tool_name in tool_names
                and tool_name not in selected_tools
            ):
                selected_tools.append(
                    tool_name
                )

        return AgentDecision(
            action="retrieve",
            selected_tools=selected_tools,
            tickers=tickers,
            reasoning=(
                "Select registered retrieval "
                "tools from query intent."
            ),
            requested_sources=requested_sources,
            confidence=0.90,
        )

    def generate_tool_calls(
        self,
        query: str,
        agent_decision: AgentDecision,
        previous_tool_results: list[
            dict[str, Any]
        ],
    ) -> list[ToolCall]:

        completed_tools = {
            result["tool_name"]
            for result in previous_tool_results
            if result.get("success")
        }

        calls = []

        call_number = (
            len(previous_tool_results) + 1
        )

        for tool_name in (
            agent_decision.selected_tools
        ):

            # Do not repeatedly call the same
            # deterministic retrieval tool.
            if tool_name in completed_tools:
                continue

            for ticker in (
                agent_decision.tickers
                or [None]
            ):

                arguments = {}

                if ticker:
                    arguments["ticker"] = ticker
                date_range = agent_decision.parameters.get("date_range")

                if date_range and date_range.get("type") == "latest":
                    arguments["latest"] = True

                if tool_name in {
                    "search_news",
                    "search_documents",
                }:
                    arguments["query"] = query
                    arguments["limit"] = 20

                elif tool_name in {
                    "get_prices",
                    "get_fundamental_data",
                    "get_volume",
                }:
                    arguments["limit"] = 20

                elif tool_name == "get_internal_api":
                    arguments["limit"] = 20

                calls.append(
                    ToolCall(
                        call_id=(
                            f"TC-{call_number:03d}"
                        ),
                        tool_name=tool_name,
                        arguments=arguments,
                        reason=(
                            "Retrieve evidence required "
                            "for the user query."
                        ),
                    )
                )

                call_number += 1

        return calls