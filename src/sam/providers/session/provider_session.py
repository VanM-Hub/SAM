"""Provider Session — sesi provider (read-only).

Sprint 151 — Provider Session.
Membuka/menutup sesi provider. Preview-only: tidak ada koneksi nyata.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ProviderSession:
    """Sesi provider (immutable)."""
    session_id: str
    provider_id: str
    open: bool = True
    active: bool = True
    external_calls: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "session_id": self.session_id,
            "provider_id": self.provider_id,
            "open": self.open,
            "active": self.active,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class SessionSummary:
    """Ringkasan sesi (immutable)."""
    total: int = 0
    open: int = 0
    active: int = 0
    total_external_calls: int = 0


class ProviderSessionStore:
    """Penyimpanan sesi provider. Append + read-only query."""

    def __init__(self) -> None:
        self._sessions: List[ProviderSession] = []

    def open_session(self, session_id: str, provider_id: str) -> ProviderSession:
        session = ProviderSession(session_id=session_id, provider_id=provider_id)
        self._sessions.append(session)
        return session

    def close(self, session_id: str) -> bool:
        for i, s in enumerate(self._sessions):
            if s.session_id == session_id and s.open:
                # dataclass frozen -> rebuild via replace
                from dataclasses import replace
                self._sessions[i] = replace(s, open=False, active=False)
                return True
        return False

    def get(self, session_id: str) -> Optional[ProviderSession]:
        for s in self._sessions:
            if s.session_id == session_id:
                return s
        return None

    def for_provider(self, provider_id: str) -> List[ProviderSession]:
        return [s for s in self._sessions if s.provider_id == provider_id]

    def count(self) -> int:
        return len(self._sessions)

    def summary(self) -> SessionSummary:
        return SessionSummary(
            total=len(self._sessions),
            open=sum(1 for s in self._sessions if s.open),
            active=sum(1 for s in self._sessions if s.active),
            total_external_calls=sum(s.external_calls for s in self._sessions),
        )
