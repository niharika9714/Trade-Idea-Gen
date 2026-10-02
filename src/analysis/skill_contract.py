from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class SkillContext:
    query: str
    query_intent: Any
    evidence_bundle: Any
    analysis_result: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.query:
            raise ValueError("query is required")


@dataclass
class SkillResult:
    skill_name: str
    status: str
    analysis_result: Any = None
    facts: list[Any] = field(default_factory=list)
    derived_metrics: list[Any] = field(default_factory=list)
    conclusions: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.skill_name:
            raise ValueError("skill_name is required")

        allowed_statuses = {
            "success",
            "partial",
            "no_data",
            "failed",
        }

        if self.status not in allowed_statuses:
            raise ValueError(
                f"Invalid skill status: {self.status}"
            )

        self.evidence_ids = list(
            dict.fromkeys(self.evidence_ids)
        )

        self.citations = list(
            dict.fromkeys(self.citations)
        )

        self.limitations = list(
            dict.fromkeys(self.limitations)
        )

    def to_dict(self):
        return {
            "skill_name": self.skill_name,
            "status": self.status,
            "facts": [
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
                for item in self.facts
            ],
            "derived_metrics": [
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
                for item in self.derived_metrics
            ],
            "conclusions": self.conclusions,
            "evidence_ids": self.evidence_ids,
            "citations": self.citations,
            "limitations": self.limitations,
            "metadata": self.metadata,
        }


@dataclass
class SkillSpec:
    name: str
    description: str
    required_intents: list[str]
    required_tools: list[str]
    execute_function: Callable[[SkillContext], SkillResult]
    trigger_keywords: list[str] = field(default_factory=list)
    priority: int = 100

    def __post_init__(self):
        if not self.name:
            raise ValueError("Skill name is required")

        if not callable(self.execute_function):
            raise TypeError(
                "execute_function must be callable"
            )

        self.required_intents = list(
            dict.fromkeys(self.required_intents)
        )

        self.required_tools = list(
            dict.fromkeys(self.required_tools)
        )

        self.trigger_keywords = list(
            dict.fromkeys(self.trigger_keywords)
        )

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "required_intents": self.required_intents,
            "required_tools": self.required_tools,
            "trigger_keywords": self.trigger_keywords,
            "priority": self.priority,
        }