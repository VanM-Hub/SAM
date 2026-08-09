"""Workspace Explainability - WP-08 (MISSION-4.6 / IP-4.6-001).

Menjelaskan asal-usul seluruh informasi yang ditampilkan pada Workspace.
Source attribution, capability trace, evidence navigation. Read-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class SourceAttribution:
    """Atribusi sumber informasi."""

    item_id: str
    source_capability: str
    source_kind: str = "capability"

    def as_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "source_capability": self.source_capability,
            "source_kind": self.source_kind,
        }


@dataclass(frozen=True)
class CapabilityTrace:
    """Trace capability asal."""

    capability_id: str
    provided_by: str  # bounded context

    def as_dict(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "provided_by": self.provided_by,
        }


@dataclass(frozen=True)
class WorkspaceExplanation:
    """Penjelasan asal-usul info di workspace."""

    view_name: str
    items: Tuple[SourceAttribution, ...] = field(default_factory=tuple)
    capability_traces: Tuple[CapabilityTrace, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "view_name": self.view_name,
            "items": [i.as_dict() for i in self.items],
            "capability_traces": [c.as_dict() for c in self.capability_traces],
        }


class WorkspaceExplainer:
    """Menjelaskan asal-usul info (read-only)."""

    # Mapping capability -> bounded context
    CAPABILITY_SOURCE = {
        "investigation": "operational_intelligence",
        "execution": "execution_runtime",
        "learning": "operational_learning",
        "reasoning": "governed_reasoning",
        "autonomous": "autonomous_operations",
    }

    def explain_view(
        self,
        view_name: str,
        capabilities: Tuple[str, ...] = (),
        items: Tuple[SourceAttribution, ...] = (),
    ) -> WorkspaceExplanation:
        traces = tuple(
            CapabilityTrace(
                capability_id=cap,
                provided_by=self.CAPABILITY_SOURCE.get(cap, "platform"),
            )
            for cap in capabilities
        )
        return WorkspaceExplanation(
            view_name=view_name, items=items, capability_traces=traces
        )
