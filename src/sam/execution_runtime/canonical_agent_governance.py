"""Canonical Agent Governance - M5 (Canonical Execution Consolidation).

Mengarahkan agent (contract `universal_agent`) untuk bertindak HANYA lewat
canonical `RealExecutionHarness` — governed, gated, audited. Agent TIDAK pernah
memegang reference ke adapter/connector langsung; ia hanya memanggil
`request_capability()` yang melewati gate P2-B.

Prinsip kunci (sejalan P7 yang sudah PROVEN):
- Agent sendiri bukan executor; ia konsumen capability.
- Setiap aksi agent harus lolos gate (capability/registry/contract/policy/approval/
  boundary/verification/audit).
- Bypass (agent mencoba memakai jalur non-approved) -> DITOLAK + audit denial.
- Contract `universal_agent.AgentInteractionContract` diserap sebagai kontrak
  canonical (non-destruktif).

Non-destruktif: file `universal_agent/*` tetap sebagai LEGACY.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    ExecutionRuntimeResult,
    RealExecutionHarness,
)


@dataclass(frozen=True)
class CanonicalAgentContract:
    """Kontrak agent canonical (normalisasi dari AgentInteractionContract universal_agent)."""

    agent_id: str
    contract_id: str
    allowed_capabilities: Tuple[str, ...]
    governed: bool = True

    def allows(self, capability: str) -> bool:
        return capability in self.allowed_capabilities

    def as_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "contract_id": self.contract_id,
            "allowed_capabilities": list(self.allowed_capabilities),
            "governed": self.governed,
        }


def from_universal_agent_contract(contract: Any) -> Optional[CanonicalAgentContract]:
    """Serap `universal_agent.AgentInteractionContract` / dict jadi canonical."""
    if contract is None:
        return None

    def _get(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    agent_id = _get(contract, "agent_id")
    contract_id = _get(contract, "contract_id")
    if not agent_id or not contract_id:
        return None

    caps: list = []
    for c in (_get(contract, "capabilities", ()) or ()):
        value = getattr(c, "value", c)
        if isinstance(value, str):
            caps.append(value)
    return CanonicalAgentContract(
        agent_id=str(agent_id),
        contract_id=str(contract_id),
        allowed_capabilities=tuple(caps),
        governed=bool(_get(contract, "governed", True)),
    )


class RealCanonicalAgent:
    """Agent governed yang bertindak HANYA via RealExecutionHarness canonical.

    Agent memegang kontrak canonical + referensi harness (bukan adapter).
    Semua aksi lewat `request_capability()` -> gate P2-B -> real execution.
    """

    def __init__(
        self,
        agent_id: str,
        harness: RealExecutionHarness,
        audit: Optional[AuditTrail] = None,
        contract: Optional[CanonicalAgentContract] = None,
    ) -> None:
        self.agent_id = agent_id
        self._harness = harness
        self._audit = audit or harness._audit  # noqa: SLF001
        self.contract = contract or CanonicalAgentContract(
            agent_id=agent_id, contract_id=f"ct-agent-{agent_id}", allowed_capabilities=()
        )

    def request_capability(
        self,
        capability: str,
        action: str,
        target: str,
        params: Optional[Dict[str, Any]] = None,
        approval_reason: str = "",
        timeout_seconds: float = 10.0,
    ) -> ExecutionRuntimeResult:
        """Satu-satunya jalur aksi: lewat harness canonical (governed)."""
        # Kontrak agent harus mengizinkan capability ini
        if not self.contract.allows(capability):
            self._audit.record("agent.contract.denied", self.agent_id,
                               capability=capability, reason="capability not in contract")
            return self._deny(capability, target, "contract not allow capability")

        operation = f"tool/{action}" if action and not action.startswith("tool/") and action != "agent" else action
        req = ExecutionRequest(
            operation=operation,
            target=target,
            params=params or {},
            mode=ExecutionMode.EXECUTE,
            correlation_id=f"agent-{self.agent_id}-{capability}",
            timeout_seconds=timeout_seconds,
            approval_reason=approval_reason,
        )
        result = self._harness.execute(req)
        if not result.outcome.get("ok") or result.outcome.get("blocked"):
            self._audit.record("agent.capability.denied", self.agent_id,
                               capability=capability, target=target,
                               blocked_by=result.outcome.get("blocked_by", []))
        return result

    def _deny(self, capability: str, target: str, reason: str) -> ExecutionRuntimeResult:
        """Tolak tanpa eksekusi (contract violation) -> no external effect."""
        return ExecutionRuntimeResult(
            outcome={
                "ok": False, "mode": "EXECUTE", "external_side_effect": False,
                "blocked": True, "blocked_by": ["contract"], "detail": reason,
                "blocked_reason": reason,
            },
            correlation_id=f"agent-{self.agent_id}-{capability}",
            started_at="", finished_at="", duration_ms=0,
            external_effect=False,
            verification={"mode": "EXECUTE", "checked": False, "blocked": True, "agent_contract": "denied"},
            audit=[e.to_dict() for e in self._audit.entries] if hasattr(self._audit, "entries") else [],
        )

    def is_bypassed(self, capability: str) -> bool:
        """Bendera: agent mencoba aksi di luar jalur canonical (bypass)."""
        # RealCanonicalAgent TIDAK punya akses adapter; semua lewat harness.
        # Ini hanya penanda defensif: agent tak punya jalur lain.
        return False


def build_agent(
    agent_id: str,
    harness: RealExecutionHarness,
    contract: Optional[CanonicalAgentContract] = None,
    audit: Optional[AuditTrail] = None,
) -> RealCanonicalAgent:
    """Fabrikasi agent governed canonical."""
    return RealCanonicalAgent(agent_id, harness, audit=audit, contract=contract)
