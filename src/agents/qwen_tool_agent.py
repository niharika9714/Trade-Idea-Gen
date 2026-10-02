from __future__ import annotations

from typing import Any

import ollama

from src.agents.agent_action import AgentAction
from src.agents.ollama_tool_schema import to_ollama_tools


OLLAMA_MODEL = "qwen3:8b"


SYSTEM_PROMPT = """
You are the reasoning agent for an internal investment research and information system.

Your job is to understand the user's request and use the registered tools to obtain
the evidence required to answer it.

IMPORTANT RULES:

1. Understand the user's request semantically.
2. Do NOT rely on predefined keyword-to-tool mappings.
3. Do NOT assume a fixed list of intents.
4. Do NOT assume that entities must be financial companies or known tickers.
5. Choose tools based on their descriptions and the information required.
6. You may call multiple tools.
7. After receiving a tool result, inspect it and decide whether more evidence is needed.
8. If more evidence is required, call another appropriate registered tool.
9. If the available evidence is sufficient, finish.
10. Do not invent facts, numbers, dates, events or sources.
11. Do not perform unsupported calculations yourself when a deterministic data tool
    can provide the required inputs.
12. Do not access files, databases, APIs or the filesystem directly.
13. Use only the registered tools.
14. Preserve the user's requested date range or period.
15. For questions about arbitrary people, documents or textual entities, use
    document-content search when appropriate.
16. For financial questions, use the appropriate market, fundamental, news,
    document or analytical tools.
17. For comparison questions, retrieve the evidence for all relevant entities.
18. Do not stop merely because the first tool returned some evidence. Determine
    whether that evidence actually answers the complete question.
19. Do not expose internal implementation details in the final answer.

The objective is evidence completeness, not simply making a tool call.

EVIDENCE-AWARE DECISION RULES

After every tool call, inspect the returned evidence before deciding what to do next.

Do not finish merely because a tool call succeeded.

Finish only when the retrieved evidence is sufficient to answer the user's question.

If the evidence is missing, empty, irrelevant, incomplete, or does not answer an important part of the question, make another appropriate tool call.

When the question has multiple parts, verify that the evidence covers all important parts before finishing.

For comparison questions involving multiple entities, retrieve evidence for all relevant entities before finishing.

For questions involving an event and its consequences, retrieve evidence for both the event and the relevant consequence when needed.

For questions involving a calculation, retrieve the underlying observations required for that calculation. Do not invent missing observations.

If a tool returns no useful evidence, do not treat the absence of evidence as an answer. Try another appropriate registered tool when one exists.

Do not call additional tools merely to increase the amount of evidence. Stop when the available evidence is sufficient.

Never invent evidence, facts, dates, values, citations, or source content.

When sufficient evidence exists, use action="finish".

ANALYTICAL TOOL RULES:

Retrieval tools provide source evidence.

Analytical tools perform deterministic calculations from
structured source data.

When the user's question requires a numerical calculation,
do not calculate the result yourself from raw evidence.

Instead:

1. Retrieve the required source data if necessary.
2. Select the appropriate analytical tool.
3. Inspect its deterministic result.
4. Only then finish the response.

Never invent numerical calculations.

Examples of analytical requirements include:
- price change
- percentage return
- period performance
- other calculations explicitly supported by registered tools.

The Python analytical tool is authoritative for the calculated value.

Do not perform arithmetic yourself when a registered analytical
tool can perform the calculation.
"""


class QwenToolAgent:
    def __init__(
        self,
        model: str = OLLAMA_MODEL,
        temperature: float = 0.0,
        think: bool = True,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.think = think

    def _initial_messages(self, query: str) -> list[dict[str, Any]]:
        return [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": query,
            },
        ]

    def decide(
        self,
        query: str,
        tool_definitions: list[dict[str, Any]],
        messages: list[dict[str, Any]] | None = None,
    ):
        conversation = list(messages) if messages is not None else self._initial_messages(query)

        ollama_tools = to_ollama_tools(tool_definitions)

        response = ollama.chat(
            model=self.model,
            messages=conversation,
            tools=ollama_tools,
            think=self.think,
            options={
                "temperature": self.temperature,
            },
        )

        response_message = response.message

        # Keep the exact assistant message so Ollama can continue the
        # conversation with its tool-call state intact.
        conversation.append(response_message)

        actions: list[AgentAction] = []

        tool_calls = getattr(response_message, "tool_calls", None)

        if tool_calls:
            for tool_call in tool_calls:
                function = tool_call.function

                name = function.name
                arguments = function.arguments

                if arguments is None:
                    arguments = {}

                actions.append(
                    AgentAction(
                        action="tool_call",
                        tool_name=name,
                        arguments=arguments,
                        reason="Qwen selected this tool based on the current evidence requirements.",
                    )
                )

        else:
            actions.append(
                AgentAction(
                    action="finish",
                    reason="Qwen determined that the available evidence is sufficient.",
                )
            )

        return response, actions, conversation