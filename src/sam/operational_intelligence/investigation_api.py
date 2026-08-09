"""Investigation API - WP-07 (MISSION-4.2 / IP-4.2-001).

Menyediakan antarmuka standar untuk capability investigasi. API bersifat
read-only, konsisten, dapat diintegrasikan, dan tidak melakukan mutation.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .evidence_collection import EvidenceRepository
from .investigation_model import (
    Investigation,
)
from .investigation_session import InvestigationSessionManager
from .investigation_timeline import InvestigationTimeline, TimelineViewer


class InvestigationNotFoundError(Exception):
    def __init__(self, investigation_id: str) -> None:
        super().__init__(f"Investigation not found: {investigation_id}")
        self.investigation_id = investigation_id


class InvestigationQuery:
    """Query investigasi (read-only, deterministik)."""

    def __init__(
        self,
        *,
        state: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> None:
        self.state = state
        self.target_id = target_id

    def matches(self, investigation: Investigation) -> bool:
        if self.state and investigation.state != self.state:
            return False
        if self.target_id:
            scope = investigation.scope
            if scope is None or not scope.contains(self.target_id):
                return False
        return True


class InvestigationResultAPI:
    """API hasil investigasi (read-only)."""

    def as_dict(self) -> dict:
        raise NotImplementedError


class InvestigationAPI:
    """Public read-only facade untuk capability investigasi."""

    def __init__(
        self,
        *,
        sessions: InvestigationSessionManager,
        evidences: EvidenceRepository,
        investigations: Dict[str, Investigation],
        timelines: Dict[str, InvestigationTimeline],
    ) -> None:
        self._sessions = sessions
        self._evidences = evidences
        self._investigations = investigations
        self._timelines = timelines

    # --- Session API ---
    def list_sessions(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(
            s.as_dict() for s in self._sessions.list_sessions()
        )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        return session.as_dict() if session else None

    # --- Investigation Query ---
    def query_investigations(
        self, query: Optional[InvestigationQuery] = None
    ) -> Tuple[Dict[str, Any], ...]:
        investigations = self._collect_investigations()
        q = query or InvestigationQuery()
        return tuple(i.as_dict() for i in investigations if q.matches(i))

    def get_investigation(
        self, investigation_id: str
    ) -> Dict[str, Any]:
        investigations = self._collect_investigations()
        for i in investigations:
            if i.investigation_id == investigation_id:
                return i.as_dict()
        raise InvestigationNotFoundError(investigation_id)

    # --- Evidence API ---
    def list_evidence(self, investigation_id: str) -> Tuple[Dict[str, Any], ...]:
        return tuple(
            e.as_dict() for e in self._evidences.get(investigation_id)
        )

    def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        ev = self._evidences.get_by_id(evidence_id)
        return ev.as_dict() if ev else None

    # --- Timeline API ---
    def get_timeline(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        tl = self._timelines.get(investigation_id)
        return TimelineViewer.view(tl) if tl else None

    def _collect_investigations(self) -> Tuple[Investigation, ...]:
        return tuple(self._investigations.values())
