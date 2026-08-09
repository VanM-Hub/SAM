"""Operational Context - WP-06 (MISSION-4.6 / IP-4.6-001).

Context operasional yang konsisten di seluruh Workspace. Context dipertahankan
selama Session, konsisten antar Workspace, dapat ditelusuri, immutable selama
satu aktivitas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class OperationalContextModel:
    """Model context operasional (immutable per aktivitas)."""

    mission_id: str = ""
    investigation_id: str = ""
    execution_id: str = ""
    learning_id: str = ""
    provider_id: str = ""
    snapshot: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "investigation_id": self.investigation_id,
            "execution_id": self.execution_id,
            "learning_id": self.learning_id,
            "provider_id": self.provider_id,
            "snapshot": self.snapshot,
        }


class ContextSync:
    """Sinkronisasi context antar aktivitas (immutable update)."""

    @staticmethod
    def with_mission(ctx: OperationalContextModel, mission_id: str) -> OperationalContextModel:
        return OperationalContextModel(
            mission_id=mission_id,
            investigation_id=ctx.investigation_id,
            execution_id=ctx.execution_id,
            learning_id=ctx.learning_id,
            provider_id=ctx.provider_id,
            snapshot=ctx.snapshot,
        )

    @staticmethod
    def with_investigation(ctx: OperationalContextModel, investigation_id: str) -> OperationalContextModel:
        return OperationalContextModel(
            mission_id=ctx.mission_id,
            investigation_id=investigation_id,
            execution_id=ctx.execution_id,
            learning_id=ctx.learning_id,
            provider_id=ctx.provider_id,
            snapshot=ctx.snapshot,
        )


class ContextManager:
    """Manajer context konsisten."""

    def __init__(self) -> None:
        self._current = OperationalContextModel()

    def set(self, context: OperationalContextModel) -> None:
        self._current = context

    def current(self) -> OperationalContextModel:
        return self._current

    def update(self, **kwargs: str) -> OperationalContextModel:
        current = self._current
        updated = OperationalContextModel(
            mission_id=kwargs.get("mission_id", current.mission_id),
            investigation_id=kwargs.get("investigation_id", current.investigation_id),
            execution_id=kwargs.get("execution_id", current.execution_id),
            learning_id=kwargs.get("learning_id", current.learning_id),
            provider_id=kwargs.get("provider_id", current.provider_id),
            snapshot=current.snapshot,
        )
        self._current = updated
        return updated
