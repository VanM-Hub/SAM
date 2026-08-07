"""Simulation Evidence (Program G - Execution Evolution, 2026-08-07).

Exec: Zara, Lead Implementation Engineer. Arah: Simon/Architect (2026-08-07).

Simulation V1 = metadata-based simulation. Evidence dihitung SECARA
DETERMINISTIK dari artefak governance yang sudah dimiliki runtime
(mission, workflow, capability, registry, contract, approval context,
execution plan, provider metadata). TIDAK menggunakan mock execution
engine, TIDAK memanggil provider, TIDAK menghasilkan external calls.

Evidence ini OPSIONAL untuk Approval (kontrak ApprovalDecision/ApprovalGate
TIDAK diubah - ADR-001 tetap berlaku). Ia memperkaya decision quality dan
auditability, bukan mewajibkan satu mekanisme implementasi.

Prinsip SAM: Govern Capability, Never Implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True)
class SimulationEvidence:
    """Evidence simulasi deterministik dari metadata governance (immutable).

    Semua field berasal dari artefak yang sudah dimiliki runtime:
    capability resolution, provider selection, contract, execution plan,
    dan metadata provider. Tidak ada hasil eksekusi/provider response.
    """

    simulation_id: str
    execution_id: str
    provider_id: str
    operation: str

    # --- Keputusan goverance yang ter-resolve ---
    capability_resolved: bool = True
    provider_selected: str = ""
    approval_required: bool = True

    # --- Estimasi deterministik (dari metadata, bukan eksekusi) ---
    estimated_external_calls: int = 0
    estimated_cost: float = 0.0
    estimated_risk: float = 0.0  # 0.0 (safe) .. 1.0 (high)
    estimated_duration_ms: float = 0.0

    # --- Analisis konsekuensi ---
    rollback_possible: bool = True
    side_effects: Tuple[str, ...] = field(default_factory=tuple)
    expected_artifact: str = ""
    expected_audit_chain: Tuple[str, ...] = field(default_factory=tuple)

    # --- Confidence ---
    confidence: float = 0.0  # 0.0 .. 1.0

    # --- Berasal dari mana (transparansi/auditability) ---
    evidence_source: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "simulation_id": self.simulation_id,
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "capability_resolved": self.capability_resolved,
            "provider_selected": self.provider_selected,
            "approval_required": self.approval_required,
            "estimated_external_calls": self.estimated_external_calls,
            "estimated_cost": self.estimated_cost,
            "estimated_risk": self.estimated_risk,
            "estimated_duration_ms": self.estimated_duration_ms,
            "rollback_possible": self.rollback_possible,
            "side_effects": list(self.side_effects),
            "expected_artifact": self.expected_artifact,
            "expected_audit_chain": list(self.expected_audit_chain),
            "confidence": self.confidence,
            "evidence_source": list(self.evidence_source),
        }
