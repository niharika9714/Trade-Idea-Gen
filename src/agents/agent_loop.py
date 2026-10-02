from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pptx import action, exc
from typing_extensions import runtime

from src.agents.agent_action import AgentAction
from src.agents.agent_tool_runtime import AgentToolRuntime
from src.agents.qwen_tool_agent import QwenToolAgent
from src.provenance.evidence import EvidenceBundle
from src.agents.evidence_context import build_evidence_context


@dataclass
class AgentLoopResult:
    query: str
    status: str
    iterations: int
    actions: list[dict[str, Any]] = field(default_factory=list)
    evidence_bundle: EvidenceBundle = field(default_factory=EvidenceBundle)
    messages: list[dict[str, Any]] = field(default_factory=list)
    final_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentLoop:
    def __init__(
        self,
        agent: QwenToolAgent | None = None,
        max_iterations: int = 6,
    ) -> None:
        self.agent = agent or QwenToolAgent()
        self.max_iterations = max_iterations

    @staticmethod
    def _merge_evidence(
        target: EvidenceBundle,
        raw_result: Any,
    ) -> None:
        if isinstance(raw_result, EvidenceBundle):
            target.merge(raw_result)



    @staticmethod
    def _serialise_tool_result(
        execution: dict[str, Any],
    ) -> str:
        """
        Convert a tool execution result into compact context for Qwen.

        Full EvidenceBundle remains preserved separately in the agent state.
        Qwen receives only a compact evidence representation so that
        tool-result context does not grow uncontrollably.
        """

        raw_result = execution.get("raw_result")

        if isinstance(raw_result, EvidenceBundle):
            return build_evidence_context(raw_result)

        result = execution.get("result")

        import json

        return json.dumps(
            result,
            ensure_ascii=False,
            default=str,
        )[:8000]

    @staticmethod
    def _assistant_message_content(response: Any) -> str:
        message = getattr(response, "message", None)

        if message is None:
            return ""

        return getattr(message, "content", "") or ""

    def run(
        self,
        query: str,
        tool_definitions: list[dict[str, Any]],
    ) -> AgentLoopResult:

        runtime = AgentToolRuntime(tool_definitions)

        evidence_bundle = EvidenceBundle()

        messages: list[dict[str, Any]] | None = None

        all_actions: list[dict[str, Any]] = []

        final_message = ""

        for iteration in range(1, self.max_iterations + 1):

            response, actions, messages = self.agent.decide(
                query=query,
                tool_definitions=tool_definitions,
                messages=messages,
            )

            for action in actions:

                all_actions.append(
                    {
                        "iteration": iteration,
                        **action.to_dict(),
                    }
                )

                if action.is_finish:
                    final_message = self._assistant_message_content(response)

                    return AgentLoopResult(
                        query=query,
                        status="completed",
                        iterations=iteration,
                        actions=all_actions,
                        evidence_bundle=evidence_bundle,
                        messages=messages or [],
                        final_message=final_message,
                        metadata={
                            "reasoning_mode": "qwen_tool_loop",
                            "model": self.agent.model,
                        },
                    )



                try:
                    tool_execution = runtime.execute(action)
                
                except Exception as exc:
                    tool_execution = {
                        "success": False,
                        "tool_name": action.tool_name,
                        "arguments": action.arguments,
                        "error": str(exc),
                        "result": None,
                        "raw_result": None,
                    }

                else:
                    tool_execution = runtime.execute(action)

                self._merge_evidence(
                    evidence_bundle,
                    tool_execution.get("raw_result"),
                )

                tool_message = {
                    "role": "tool",
                    "tool_name": action.tool_name,
                    "content": self._serialise_tool_result(tool_execution),
                }

                if messages is None:
                    messages = []

                messages.append(tool_message)

        return AgentLoopResult(
            query=query,
            status="max_iterations",
            iterations=self.max_iterations,
            actions=all_actions,
            evidence_bundle=evidence_bundle,
            messages=messages or [],
            final_message=final_message,
            metadata={
                "reasoning_mode": "qwen_tool_loop",
                "model": self.agent.model,
                "max_iterations": self.max_iterations,
            },
        )