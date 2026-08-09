"""Investigation Model - WP-01 (MISSION-4.2 / IP-4.2-001).

Model domain untuk seluruh aktivitas investigasi operasional berbasis evidence.

Deterministic, immutable result. Investigation memiliki identitas unik, state
deterministik, scope dapat ditelusuri, dan result immutable.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _norm(value: Any) -> str:
    return str(value).strip().lower()


def _stable_hash(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(_norm(p).encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


@dataclass(frozen=True)
class InvestigationTarget:
    """Sasaran investigasi (objek yang diamati)."""

    target_type: str  # runtime | provider | workflow | mission | component
    target_id: str
    name: str = ""
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "target_type": self.target_type,
            "target_id": self.target_id,
            "name": self.name,
            "metadata": [list(m) for m in self.metadata],
        }


@dataclass(frozen=True)
class InvestigationScope:
    """Ruang lingkup investigasi (dapat ditelusuri)."""

    reason: str
    targets: Tuple[InvestigationTarget, ...] = field(default_factory=tuple)
    depth: str = "standard"  # quick | standard | deep
    include_providers: bool = False
    allowed_observers: Tuple[str, ...] = field(default_factory=tuple)

    def contains(self, target_id: str) -> bool:
        return any(t.target_id == target_id for t in self.targets)

    def as_dict(self) -> dict:
        return {
            "reason": self.reason,
            "targets": [t.as_dict() for t in self.targets],
            "depth": self.depth,
            "include_providers": self.include_providers,
            "allowed_observers": list(self.allowed_observers),
        }


class InvestigationState:
    """State machine deterministik investigasi (immutable transitions)."""

    CREATED = "created"
    SCOPE_SET = "scope_set"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    COMPLETED = "completed"

    _ORDER = (CREATED, SCOPE_SET, COLLECTING, ANALYZING, COMPLETED)

    @classmethod
    def valid(cls, state: str) -> bool:
        return state in cls._ORDER

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        if not cls.valid(current) or not cls.valid(target):
            return False
        return cls._ORDER.index(target) > cls._ORDER.index(current)


@dataclass(frozen=True)
class InvestigationMetadata:
    """Metadata investigasi (konten jenuh metadata)."""

    created_by: str = "engineering"
    purpose: str = ""
    environment: str = ""
    tags: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "created_by": self.created_by,
            "purpose": self.purpose,
            "environment": self.environment,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class InvestigationResult:
    """Hasil investigasi (immutable)."""

    investigation_id: str
    status: str
    summary: str
    created_at: str
    evidence_count: int = 0
    timeline_count: int = 0
    observations: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    result_hash: str = ""

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "status": self.status,
            "summary": self.summary,
            "created_at": self.created_at,
            "evidence_count": self.evidence_count,
            "timeline_count": self.timeline_count,
            "observations": list(self.observations),
            "result_hash": self.result_hash,
        }


@dataclass(frozen=True)
class Investigation:
    """Model investigasi operasional (identitas unik)."""

    investigation_id: str
    created_at: str
    state: str = InvestigationState.CREATED
    scope: Optional[InvestigationScope] = None
    metadata: InvestigationMetadata = field(
        default_factory=InvestigationMetadata
    )
    result: Optional[InvestigationResult] = None
    scope_hash: str = ""

    @classmethod
    def create(
        cls,
        *,
        investigation_id: Optional[str] = None,
        metadata: Optional[InvestigationMetadata] = None,
    ) -> "Investigation":
        return cls(
            investigation_id=investigation_id or uuid.uuid4().hex,
            created_at=_now_utc(),
            state=InvestigationState.CREATED,
            metadata=metadata or InvestigationMetadata(),
        )

    def with_scope(self, scope: InvestigationScope) -> "Investigation":
        if not InvestigationState.can_transition(
            self.state, InvestigationState.SCOPE_SET
        ):
            raise ValueError(f"Cannot set scope from state {self.state!r}")
        return Investigation(
            investigation_id=self.investigation_id,
            created_at=self.created_at,
            state=InvestigationState.SCOPE_SET,
            scope=scope,
            metadata=self.metadata,
            scope_hash=_stable_hash(
                scope.reason,
                scope.depth,
                scope.include_providers,
                *[t.target_id for t in scope.targets],
            ),
        )

    def with_state(self, target: str) -> "Investigation":
        if not InvestigationState.can_transition(self.state, target):
            raise ValueError(
                f"Cannot transition {self.state!r} -> {target!r}"
            )
        return Investigation(
            investigation_id=self.investigation_id,
            created_at=self.created_at,
            state=target,
            scope=self.scope,
            metadata=self.metadata,
            result=self.result,
            scope_hash=self.scope_hash,
        )

    def with_result(self, result: InvestigationResult) -> "Investigation":
        if self.state != InvestigationState.ANALYZING:
            raise ValueError(
                f"Result only from ANALYZING, got {self.state!r}"
            )
        return Investigation(
            investigation_id=self.investigation_id,
            created_at=self.created_at,
            state=InvestigationState.COMPLETED,
            scope=self.scope,
            metadata=self.metadata,
            result=result,
            scope_hash=self.scope_hash,
        )

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "created_at": self.created_at,
            "state": self.state,
            "scope": self.scope.as_dict() if self.scope else None,
            "metadata": self.metadata.as_dict(),
            "result": self.result.as_dict() if self.result else None,
            "scope_hash": self.scope_hash,
        }
