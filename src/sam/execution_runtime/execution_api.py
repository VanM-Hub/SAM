"""Execution API - IP-4.1-002 WP-17.

Governed Execution.
Public API (read-only) untuk mengakses jalur execution yang di-govern.

Scope (Foundation immutable):
- Menyediakan akses capability execution secara resmi.
- Tidak melakukan approval decision (Article XVI: Presentation tidak approve).
- Approval datang dari Governance, bukan dari API layer.
- Deterministik & dapat diaudit.

Tidak ada network, tidak menambah authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .execution_request import ExecutionRequest
from .governed_execution import GovernedExecution, GovernedExecutionResult
from .credential_verifier import CredentialVerifier, VerificationSummary
from .provider_connection import ProviderConnectionManager
from .execution_audit import AuditSummary


@dataclass(frozen=True)
class ExecutionAPIStatus:
    """Status API execution (immutable)."""

    total_records: int
    executed: int
    blocked: int
    verified_providers: int
    connected_providers: int
    available_providers: int

    def as_dict(self) -> dict:
        return {
            "total_records": self.total_records,
            "executed": self.executed,
            "blocked": self.blocked,
            "verified_providers": self.verified_providers,
            "connected_providers": self.connected_providers,
            "available_providers": self.available_providers,
        }


class ExecutionAPI:
    """Public API execution (read-only facade).

    Membungkus GovernedExecution + credential/connection status untuk
    operator/presentation tanpa membuka authority.
    """

    def __init__(
        self,
        governed: Optional[GovernedExecution] = None,
        verifier: Optional[CredentialVerifier] = None,
        connection: Optional[ProviderConnectionManager] = None,
    ) -> None:
        self._governed = governed or GovernedExecution()
        self._verifier = verifier or CredentialVerifier()
        self._connection = connection or ProviderConnectionManager(verifier=self._verifier)

    # -- Jalur utama --
    def execute(self, request: ExecutionRequest, policy_id: str = "") -> GovernedExecutionResult:
        """Jalankan (atau coba) execution lewat jalur governed. Approval tetap gate."""
        return self._governed.execute(request, policy_id)

    # -- Read-only status --
    def status(self) -> ExecutionAPIStatus:
        audit = self._governed.audit
        summary: AuditSummary = audit.summary()
        v_summary: VerificationSummary = self._verifier.summary()
        conn = self._connection.summary()
        return ExecutionAPIStatus(
            total_records=summary.total,
            executed=summary.executed,
            blocked=summary.blocked,
            verified_providers=v_summary.verified,
            connected_providers=conn.get("connected", 0),
            available_providers=conn.get("total", 0),
        )

    def audit_summary(self) -> AuditSummary:
        return self._governed.audit.summary()

    def credential_summary(self) -> VerificationSummary:
        return self._verifier.summary()

    def provider_status(self, actor: str = "execution") -> Tuple[str, ...]:
        """Provider yang siap dieksekusi (connected)."""
        return self._connection.connected_providers(actor)

    def audit_record(self, execution_id: str):
        return self._governed.audit.get(execution_id)
