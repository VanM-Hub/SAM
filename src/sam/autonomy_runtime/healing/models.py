# Self-Healing Model - WP-24
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# Immutable model proposal self-healing. healing/ hanya berisi PLN & model
# PROPOSAL - tidak pernah executor / mutation. Prinsip: "Recover by strategy,
# never by authority." Runtime TIDAK melakukan self-healing otomatis; hanya
# menyusun candidate plan.

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class HealingStep:
    """Satu langkah self-healing yang DIUSULKAN (bukan eksekusi)."""

    step_id: str
    action: str  # label tindakan yang diusulkan (recover_*), bukan eksekusi
    target: str
    strategy: str
    prerequisite_ids: Tuple[str, ...] = ()
    priority: int = 0
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "target": self.target,
            "strategy": self.strategy,
            "prerequisite_ids": list(self.prerequisite_ids),
            "priority": self.priority,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SelfHealingPlan:
    """Candidate self-healing plan - immutable, proposal-only.

    Menyusun urutan langkah self-healing yang DIUSULKAN berdasarkan strategi
    recovery. Tidak pernah mengeksekusi apa pun terhadap runtime, tidak
    memodifikasi Mission/Workflow/Policy/Governance, tidak menjalankan
    rollback/restart. Hanya proposal deterministik.
    """

    plan_id: str
    context_state_id: str
    strategy_id: str
    steps: Tuple[HealingStep, ...] = ()
    state: str = "proposed"  # proposed
    readiness_gate: str = "ready"
    rationale: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "context_state_id": self.context_state_id,
            "strategy_id": self.strategy_id,
            "steps": [s.as_dict() for s in self.steps],
            "state": self.state,
            "readiness_gate": self.readiness_gate,
            "rationale": self.rationale,
            "metadata": dict(self.metadata),
        }

    def step_count(self) -> int:
        return len(self.steps)

    def step_ids(self) -> list:
        return [s.step_id for s in self.steps]

    def is_proposal_only(self) -> bool:
        """Plan ini murni proposal - semua langkah ber-label recover_/heal_."""
        return all(s.action.startswith("recover_") or s.action.startswith("heal_") for s in self.steps)
