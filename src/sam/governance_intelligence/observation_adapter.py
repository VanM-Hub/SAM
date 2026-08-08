"""governance_intelligence.observation_adapter — WP-11 (IP-3.1-001).

Reuse Program C (Observation Layer). The adapter READS Observation output
and feeds it into Knowledge -> Reasoning. It never modifies the Observation
Layer, never mutates runtime, and keeps the dependency direction
governance_intelligence -> sam.observation (see Dependency Rules).

The observation layer already publishes read-only reports; this adapter maps
those reports into KnowledgeItem-like evidence so the Governance Reasoner
(WP-05) and Intelligence Gateway (WP-10) can cite them.

Import is defensive: if the Observation Layer is unavailable at runtime, the
adapter degrades gracefully instead of crashing the framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.governance_intelligence.knowledge.models import KnowledgeItem


@dataclass(frozen=True)
class ObservationFeed:
    """Normalized view of observation-layer output for the reasoning layer."""

    source: str
    entries: List[KnowledgeItem] = field(default_factory=list)

    def size(self) -> int:
        return len(self.entries)

    def all(self) -> List[KnowledgeItem]:
        return list(self.entries)


class ObservationAdapter:
    """WP-11 implementation. Read-only bridge into the Observation Layer."""

    def __init__(self) -> None:
        self._obs = None
        try:
            import sam.observation as obs  # type: ignore

            self._obs = obs
            self._available = True
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def feed(self, source: str) -> ObservationFeed:
        """Collect observation-layer reports as knowledge items.

        Contributes health, workflow, and approval observations only if the
        Observation Layer is importable. Never raises when it is absent.
        """
        if not self._available or self._obs is None:
            return ObservationFeed(source=source, entries=[])

        entries: List[KnowledgeItem] = []
        idx = 0

        # Mission health
        obs = getattr(self._obs, "MissionIntelligenceObserver", None)
        if obs is not None:
            try:
                report = obs().report()
                text = self._serialize(report)
                entries.append(self._item(source, "observation.mission", "MissionHealth", text))
                idx += 1
            except Exception:
                pass

        # Workflow
        obs = getattr(self._obs, "WorkflowIntelligenceObserver", None)
        if obs is not None:
            try:
                report = obs().report()
                text = self._serialize(report)
                entries.append(self._item(source, "observation.workflow", "WorkflowState", text))
                idx += 1
            except Exception:
                pass

        # Approval
        obs = getattr(self._obs, "ApprovalIntelligenceObserver", None)
        if obs is not None:
            try:
                report = obs().report()
                text = self._serialize(report)
                entries.append(self._item(source, "observation.approval", "ApprovalQueue", text))
                idx += 1
            except Exception:
                pass

        return ObservationFeed(source=source, entries=entries)

    @staticmethod
    def _item(source: str, key: str, title: str, content: str) -> KnowledgeItem:
        import hashlib

        sig = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return KnowledgeItem(
            key=key,
            kind="observation",
            source=source,
            section=title,
            title=title,
            content=content,
            signature=sig,
            metadata={"layer": "observation"},
        )

    @staticmethod
    def _serialize(obj: Any) -> str:
        """Best-effort string projection of an observation DTO."""
        if obj is None:
            return "no data"
        if hasattr(obj, "public_dict"):
            d = obj.public_dict()
        elif isinstance(obj, dict):
            d = obj
        else:
            d = {"output": str(obj)}
        return "\n".join(f"{k}: {v}" for k, v in d.items())
