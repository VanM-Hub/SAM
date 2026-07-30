"""Runtime Security — DTOs keamanan runtime."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class SecurityPolicy:
    policy_id: str
    name: str
    rules: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass(frozen=True)
class AccessControl:
    access_id: str
    subject: str
    resource: str
    permission: str = "read"
    granted: bool = False


@dataclass(frozen=True)
class AuditEntry:
    entry_id: str
    action: str
    subject: str = ""
    resource: str = ""
    timestamp: float = 0.0


@dataclass(frozen=True)
class SecurityVerdict:
    verdict_id: str
    allowed: bool = False
    reason: str = ""
