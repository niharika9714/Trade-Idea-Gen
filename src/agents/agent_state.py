from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentState:
    """
    State carried through the agentic workflow.

    Step 3A intentionally keeps this state independent of
    any specific LLM provider.
    """

    query: str

    query_intent: Optional[Any] = None
    retrieval_plan: Optional[Any] = None

    evidence_bundle: Optional[Any] = None
    analysis_result: Optional[Any] = None

    reasoning_result: Optional[Any] = None
    answer_result: Optional[Any] = None

    agent_decision: Optional[Any] = None

    skill_decision: Any = None
    skill_results: list[Any] = field(
        default_factory=list
    )

    messages: list[dict[str, str]] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def add_message(
        self,
        role: str,
        content: Any,
    ):
        if role not in {
            "system",
            "user",
            "assistant",
            "tool",
            "skill_selector",
            "skill",
        }:
            raise ValueError(
                f"Unsupported message role: {role}"
            )
    
        self.messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    def to_dict(self):
        return {
            "query": self.query,
            "query_intent": (
                self.query_intent.to_dict()
                if hasattr(self.query_intent, "to_dict")
                else self.query_intent
            ),
            "retrieval_plan": (
                self.retrieval_plan.__dict__
                if self.retrieval_plan is not None
                else None
            ),
            "agent_decision": (
                self.agent_decision.to_dict()
                if hasattr(self.agent_decision, "to_dict")
                else self.agent_decision
            ),
            "reasoning_result": (
                self.reasoning_result.to_dict()
                if self.reasoning_result is not None
                and hasattr(self.reasoning_result, "to_dict")
                else self.reasoning_result
            ),
            
            "answer_result": (
                self.answer_result.to_dict()
                if self.answer_result is not None
                and hasattr(self.answer_result, "to_dict")
                else self.answer_result
            ),
            "skill_decision": (
                self.skill_decision
            ),
            "skill_results": [
                result.to_dict()
                if hasattr(result, "to_dict")
                else result
                for result in self.skill_results
            ],
            "messages": list(self.messages),
            "metadata": self.metadata,
        }