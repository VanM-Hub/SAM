"""Agent Validator — validasi agent runtime (Sprint 163).

Agent Runtime — memvalidasi kepatuhan terhadap konstrain.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .agent_certification import AgentCertification  # noqa: F401


@dataclass(frozen=True)
class AgentValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class AgentValidator:
    """Validator agent. Deterministik."""

    def validate(
        self,
        frozen: bool = True,
        synchronous: bool = True,
        no_execution: bool = True,
        bridges_readonly: bool = True,
    ) -> AgentValidation:
        issues = []
        if not frozen:
            issues.append("DTO not frozen")
        if not synchronous:
            issues.append("not synchronous")
        if not no_execution:
            issues.append("execution detected")
        if not bridges_readonly:
            issues.append("bridge not read-only")
        return AgentValidation(valid=not issues, issues=issues)
