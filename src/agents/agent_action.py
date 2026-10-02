from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ALLOWED_ACTIONS = {
    "tool_call",
    "finish",
}


@dataclass
class AgentAction:
    """
    One decision made by the Qwen agent.

    The agent either requests a registered tool or finishes.
    Semantic interpretation is intentionally NOT encoded here.
    """

    action: str
    tool_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def __post_init__(self) -> None:
        if self.action not in ALLOWED_ACTIONS:
            raise ValueError(
                f"Unsupported agent action: {self.action}. "
                f"Allowed actions: {sorted(ALLOWED_ACTIONS)}"
            )

        if self.action == "tool_call":
            if not self.tool_name:
                raise ValueError(
                    "tool_call requires tool_name"
                )

            if not isinstance(self.arguments, dict):
                raise ValueError(
                    "tool_call arguments must be a dictionary"
                )

        elif self.action == "finish":
            self.tool_name = None
            self.arguments = {}

    @property
    def is_tool_call(self) -> bool:
        return self.action == "tool_call"

    @property
    def is_finish(self) -> bool:
        return self.action == "finish"

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "reason": self.reason,
        }