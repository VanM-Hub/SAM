"""Model Session — sesi model (Sprint 246).

Program B — Model Runtime Integration.
In-memory, read-only, preview-only, no-network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .model_pipeline import ModelPipelineLog
from .model_report import ModelReport


@dataclass(frozen=True)
class ModelSession:
    """Sesi model (immutable terhadap static data)."""
    session_id: str
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ModelSessionStore:
    """Penyimpan sesi model in-memory. No write eksternal."""

    def __init__(self) -> None:
        self._sessions: dict = {}
        self._reports: dict = {}

    def create(self, session_id: str) -> ModelSession:
        session = ModelSession(session_id=session_id)
        self._sessions[session_id] = session
        self._reports[session_id] = []
        return session

    def get(self, session_id: str) -> Optional[ModelSession]:
        return self._sessions.get(session_id)

    def add_report(self, session_id: str, report: ModelReport) -> bool:
        if session_id not in self._reports:
            return False
        self._reports[session_id].append(report)
        return True

    def reports(self, session_id: str) -> List[ModelReport]:
        return list(self._reports.get(session_id, []))

    def count(self) -> int:
        return len(self._sessions)
