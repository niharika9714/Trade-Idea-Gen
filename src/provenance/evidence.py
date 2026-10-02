from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# ============================================================
# HELPERS
# ============================================================

def _canonical_json(value: Any) -> str:
    """
    Convert an object into deterministic JSON.

    This is important because evidence IDs must remain stable
    across repeated retrievals.
    """

    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


# ============================================================
# EVIDENCE OBJECT
# ============================================================

@dataclass
class Evidence:
    """
    Unified evidence object.

    Every source retrieved by the investment research system
    should eventually be represented by this structure.
    """

    source_type: str
    source: str
    locator: str
    content_type: str
    content: Any

    ticker: Optional[str] = None
    event_id: Optional[str] = None

    source_system: Optional[str] = None

    synthetic: bool = True

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    evidence_id: str = field(
        init=False
    )

    citation: str = field(
        init=False
    )

    retrieved_at: str = field(
        init=False
    )

    content_hash: str = field(
        init=False
    )

    def __post_init__(self):

        # ----------------------------------------------------
        # Normalize strings
        # ----------------------------------------------------

        self.source_type = str(
            self.source_type
        ).lower()

        self.source = str(
            self.source
        )

        self.locator = str(
            self.locator
        )

        self.content_type = str(
            self.content_type
        ).lower()

        if self.ticker:
            self.ticker = str(
                self.ticker
            ).upper()

        if self.event_id:
            self.event_id = str(
                self.event_id
            )

        # ----------------------------------------------------
        # Content hash
        # ----------------------------------------------------

        canonical_content = _canonical_json(
            self.content
        )

        self.content_hash = _sha256(
            canonical_content
        )

        # ----------------------------------------------------
        # Deterministic evidence ID
        #
        # IMPORTANT:
        # retrieved_at is deliberately NOT included.
        # ----------------------------------------------------

        identity = {
            "source_type": self.source_type,
            "source": self.source,
            "locator": self.locator,
            "content_hash": self.content_hash,
        }

        self.evidence_id = (
            "EV-"
            + _sha256(
                _canonical_json(identity)
            )[:20]
        )

        # ----------------------------------------------------
        # Citation
        # ----------------------------------------------------

        self.citation = (
            f"{self.source}#{self.locator}"
        )

        # ----------------------------------------------------
        # Retrieval timestamp
        #
        # Informational only.
        # Never used to calculate evidence_id.
        # ----------------------------------------------------

        self.retrieved_at = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        # ----------------------------------------------------
        # Provenance
        # ----------------------------------------------------

        self.provenance = {
            **self.provenance,

            "source_type": self.source_type,
            "source": self.source,
            "locator": self.locator,
            "content_type": self.content_type,

            "source_system": (
                self.source_system
                or self.provenance.get(
                    "source_system"
                )
            ),

            "synthetic": self.synthetic,

            "content_hash": self.content_hash,

            "evidence_id": self.evidence_id,

            "citation": self.citation,
        }

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> Dict[str, Any]:

        return {
            "evidence_id": self.evidence_id,

            "source_type": self.source_type,
            "source": self.source,
            "locator": self.locator,

            "content_type": self.content_type,

            "ticker": self.ticker,
            "event_id": self.event_id,

            "content": self.content,

            "metadata": self.metadata,

            "provenance": self.provenance,

            "citation": self.citation,

            "content_hash": self.content_hash,

            "retrieved_at": self.retrieved_at,
        }

    def to_json(self) -> str:

        return _canonical_json(
            self.to_dict()
        )


# ============================================================
# FACTORY
# ============================================================

def create_evidence(
    source_type: str,
    source: str,
    locator: str,
    content_type: str,
    content: Any,
    ticker: Optional[str] = None,
    event_id: Optional[str] = None,
    source_system: Optional[str] = None,
    synthetic: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
    provenance: Optional[Dict[str, Any]] = None,
) -> Evidence:

    return Evidence(
        source_type=source_type,
        source=source,
        locator=locator,
        content_type=content_type,
        content=content,
        ticker=ticker,
        event_id=event_id,
        source_system=source_system,
        synthetic=synthetic,
        metadata=metadata or {},
        provenance=provenance or {},
    )


# ============================================================
# EVIDENCE BUNDLE
# ============================================================

@dataclass
class EvidenceBundle:

    evidence: list[Evidence] = field(
        default_factory=list
    )

    def add(
        self,
        evidence: Evidence,
    ) -> None:

        self.evidence.append(
            evidence
        )
    def __iter__(self):
        return iter(self.evidence)

    def merge(self, other: "EvidenceBundle") -> None:
        for evidence in other:
            self.add(evidence)

    def to_dict(self):
        return {
            "evidence": [
                evidence.to_dict()
                for evidence in self.evidence
            ]
        }

    def citations(self):
        return [
            evidence.citation
            for evidence in self.evidence
        ]

    def ids(self):
        return [
            evidence.evidence_id
            for evidence in self.evidence
        ]
    