"""Provider Session — sesi provider standar (Sprint 228).

Program A — External Connector Integration.
Melacak konteks pemakaian provider secara deterministik tanpa network call.
Immutable; setiap perubahan menghasilkan instance baru.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Tuple


class ProviderSessionState(str, Enum):
    """Status sesi provider."""
    CREATED = "created"
    OPEN = "open"
    CLOSED = "closed"
    ERROR = "error"


@dataclass(frozen=True)
class ProviderSession:
    """Sesi provider immutable. State transisi via instance baru."""
    session_id: str
    provider_id: str
    state: ProviderSessionState = ProviderSessionState.CREATED
    history: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Dict[str, str] = field(default_factory=dict)
    external_calls: int = 0

    def open(self) -> "ProviderSession":
        return ProviderSession(
            self.session_id, self.provider_id, ProviderSessionState.OPEN,
            self.history, self.metadata, self.external_calls,
        )

    def close(self) -> "ProviderSession":
        return ProviderSession(
            self.session_id, self.provider_id, ProviderSessionState.CLOSED,
            self.history + ("close",), self.metadata, self.external_calls,
        )

    def record(self, event: str) -> "ProviderSession":
        return ProviderSession(
            self.session_id, self.provider_id, self.state,
            self.history + (event,), self.metadata, self.external_calls,
        )

    @property
    def is_open(self) -> bool:
        return self.state == ProviderSessionState.OPEN
