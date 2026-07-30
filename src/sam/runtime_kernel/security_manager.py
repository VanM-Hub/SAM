"""Security Manager — kelola kebijakan keamanan."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_security import SecurityPolicy, AccessControl, AuditEntry, SecurityVerdict


class SecurityManager:
    """Manager keamanan — preview-only."""

    def __init__(self) -> None:
        self._policies: Dict[str, SecurityPolicy] = {}
        self._audits: List[AuditEntry] = []

    def add_policy(self, policy: SecurityPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> SecurityPolicy | None:
        return self._policies.get(policy_id)

    def count_policies(self) -> int:
        return len(self._policies)

    def check_access(self, verdict_id: str, subject: str, resource: str,
                     permission: str) -> SecurityVerdict:
        for p in self._policies.values():
            for rule in p.rules:
                if subject in rule and resource in rule:
                    if p.enabled:
                        return SecurityVerdict(verdict_id, True, "allowed")
        return SecurityVerdict(verdict_id, False, "no matching policy")

    def audit(self, entry_id: str, action: str, subject: str = "",
              resource: str = "", timestamp: float = 0.0) -> AuditEntry:
        e = AuditEntry(entry_id, action, subject, resource, timestamp)
        self._audits.append(e)
        return e

    def get_audit_log(self) -> List[AuditEntry]:
        return list(self._audits)

    def count_audits(self) -> int:
        return len(self._audits)
