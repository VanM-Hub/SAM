"""
Session Registry.

Registry for approval sessions. No persistence.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from .approval_session import ApprovalSession, ApprovalSessionStatistics, ApprovalSessionSnapshot


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: List[ApprovalSession] = []

    def register(self, session: ApprovalSession) -> None:
        self._sessions.append(session)

    def lookup(self, session_id: str) -> Optional[ApprovalSession]:
        for s in reversed(self._sessions):
            if s.session_id == session_id: return s
        return None

    @property
    def latest(self) -> Optional[ApprovalSession]:
        return self._sessions[-1] if self._sessions else None

    @property
    def count(self) -> int:
        return len(self._sessions)

    def search(self, state_name: Optional[str] = None) -> List[ApprovalSession]:
        if not state_name: return list(self._sessions)
        return [s for s in self._sessions if s.state.name == state_name]

    def get_statistics(self) -> ApprovalSessionStatistics:
        counts = {"created":0,"validated":0,"pending":0,"active":0,"completed":0,"closed":0,"cancelled":0}
        for s in self._sessions:
            n = s.state.name.lower()
            if n in counts: counts[n] += 1
        return ApprovalSessionStatistics(total=self.count, **counts)

    def create_snapshot(self) -> ApprovalSessionSnapshot:
        stats = self.get_statistics()
        return ApprovalSessionSnapshot(snapshot_id=str(uuid.uuid4()), timestamp=datetime.now().timestamp(),
                                        sessions=list(self._sessions[-20:]), statistics=stats)
