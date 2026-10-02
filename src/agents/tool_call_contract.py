from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolCall:
    """
    Structured request from the LLM to execute one registered tool.
    """

    call_id: str
    tool_name: str

    arguments: dict[str, Any] = field(
        default_factory=dict
    )

    reason: Optional[str] = None

    def __post_init__(self):

        if not self.call_id:
            raise ValueError(
                "call_id is required"
            )

        if not self.tool_name:
            raise ValueError(
                "tool_name is required"
            )

        if not isinstance(
            self.arguments,
            dict,
        ):
            raise TypeError(
                "arguments must be a dictionary"
            )

    def to_dict(self):
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "reason": self.reason,
        }


@dataclass
class ToolExecutionResult:
    """
    Deterministic result returned by the tool executor.
    """

    call_id: str
    tool_name: str

    success: bool

    result: Any = None

    error: Optional[str] = None

    evidence_ids: list[str] = field(
        default_factory=list
    )

    citations: list[str] = field(
        default_factory=list
    )

    def __post_init__(self):

        self.evidence_ids = list(
            dict.fromkeys(
                self.evidence_ids
            )
        )

        self.citations = list(
            dict.fromkeys(
                self.citations
            )
        )

    def to_dict(self):
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "evidence_ids": self.evidence_ids,
            "citations": self.citations,
        }