from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentDecision:
    """
    Structured decision produced by the LLM.

    IMPORTANT:

    The LLM does not execute anything here.

    It declares what it believes should happen.
    The deterministic agent layer will validate this
    before any tool is executed.
    """

    action: str

    selected_tools: list[str] = field(
        default_factory=list
    )

    tickers: list[str] = field(
        default_factory=list
    )

    reasoning: Optional[str] = None

    requested_sources: list[str] = field(
        default_factory=list
    )

    confidence: Optional[float] = None

    parameters: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self):

        allowed_actions = {
            "retrieve",
            "analyse",
            "reason",
            "answer",
            "clarify",
        }

        if self.action not in allowed_actions:
            raise ValueError(
                f"Unsupported agent action: {self.action}"
            )

        self.selected_tools = list(
            dict.fromkeys(self.selected_tools)
        )

        self.tickers = list(
            dict.fromkeys(self.tickers)
        )

        self.requested_sources = list(
            dict.fromkeys(self.requested_sources)
        )

        if self.confidence is not None:

            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError(
                    "confidence must be between 0 and 1"
                )

    def to_dict(self):
        return {
            "action": self.action,
            "selected_tools": self.selected_tools,
            "tickers": self.tickers,
            "reasoning": self.reasoning,
            "requested_sources": self.requested_sources,
            "confidence": self.confidence,
            "parameters": self.parameters,
        }


@dataclass
class AgentResponse:
    """
    Final structured response envelope from the agent.

    Step 3A does not yet generate the final natural-language
    investment answer.
    """

    query: str

    decision: Optional[AgentDecision] = None

    status: str = "initialized"

    message: Optional[str] = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self):
        return {
            "query": self.query,
            "decision": (
                self.decision.to_dict()
                if self.decision
                else None
            ),
            "status": self.status,
            "message": self.message,
            "metadata": self.metadata,
        }