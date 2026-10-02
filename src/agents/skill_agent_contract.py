from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillDecision:
    skill_names: list[str] = field(default_factory=list)
    reasoning: dict[str, str] = field(
        default_factory=dict
    )
    confidence: float = 0.0

    def __post_init__(self):

        self.skill_names = list(
            dict.fromkeys(self.skill_names)
        )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

    def to_dict(self):
        return {
            "skill_names": self.skill_names,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
        }


@dataclass
class SkillExecutionResult:

    skill_name: str
    status: str

    evidence_ids: list[str] = field(
        default_factory=list
    )

    citations: list[str] = field(
        default_factory=list
    )

    result: Any = None

    error: str | None = None

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

        result = self.result

        if hasattr(result, "to_dict"):
            result = result.to_dict()

        return {
            "skill_name": self.skill_name,
            "status": self.status,
            "evidence_ids": self.evidence_ids,
            "citations": self.citations,
            "result": result,
            "error": self.error,
        }