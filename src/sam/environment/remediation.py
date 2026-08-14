"""Environment-adaptive: perencanaan remediation + governance.

SAM memilih remediation berdasarkan CAPABILITY yang benar-benar tersedia
(bukan asumsi jenis aplikasi), lalu menjalankannya HANYA lewat jalur
canonical governance/execution (AutonomousRecoveryLoop + ApprovalGate).
SAM TIDAK pernah mengeksekusi connector langsung.

Jika capability remediation tidak tersedia -> SAM jujur "tidak bisa
memperbaiki saat ini", bukan mengarang solusi.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from sam.environment.confidence import ConfidenceLevel
from sam.environment.diagnosis import DiagnosisEngine, Hypothesis
from sam.environment.entity import Entity


@dataclass
class RemediationCandidate:
    """Satu opsi remediation (belum dieksekusi)."""

    capability: str      # nama capability yang tersedia (mis. "repair_file")
    target: str          # entity id
    action_desc: str     # apa yang akan dilakukan (lewat canonical)
    available: bool      # apakah capability benar-benar tersedia
    evidence_note: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "capability": self.capability,
            "target": self.target,
            "action_desc": self.action_desc,
            "available": self.available,
            "evidence_note": self.evidence_note,
        }


class RemediationPlanner:
    """Memilih remediation berdasarkan diagnosis + capability registry.

    capability_registry: mapping capability -> (available: bool, execute_fn).
    execute_fn TIDAK dipanggil di sini; hanya ditandai sebagai tersedia.
    Eksekusi terjadi di recovery loop canonical.
    """

    def __init__(
        self,
        capability_registry: Optional[Dict[str, Callable[..., Any]]] = None,
        requirements: Optional[Dict[str, ConfidenceLevel]] = None,
    ) -> None:
        # registry: capability -> callable. Ganti None bila tak tersedia.
        self._registry: Dict[str, Callable[..., Any]] = capability_registry or {}
        # ambang confidence per capability (bila absen, default MEDIUM)
        self._requirements = requirements or {}

    def register(self, capability: str, fn: Callable[..., Any]) -> None:
        self._registry[capability] = fn

    def available_capabilities(self) -> List[str]:
        return [c for c, fn in self._registry.items() if fn is not None]

    def plan(
        self,
        target: Entity,
        hypothesis: Hypothesis,
        diagnosis_engine: DiagnosisEngine,
    ) -> List[RemediationCandidate]:
        """Pilih remediation berdasar confidence + capability tersedia.

        Aturan:
          - hypothesis tidak confident -> tidak ada remediation (jujur,
            "evidence tidak cukup" -> tidak diperbaiki asal-asalan).
          - capability yang tidak tersedia -> available=False (tidak dipilih
            untuk dijalankan). SAM jujur bahwa itu tidak tersedia.
        """
        if not hypothesis.confident:
            return []  # jangan remediasi tanpa confidence (jangan mengarang)

        req = self._requirements.get("auto", ConfidenceLevel.MEDIUM)
        if hypothesis.level != ConfidenceLevel.HIGH and req == ConfidenceLevel.HIGH:
            return []  # butuh confidence tinggi tapi tak terpenuhi -> honest skip

        candidates: List[RemediationCandidate] = []
        for capability, fn in (self._registry or {}).items():
            available = fn is not None
            candidates.append(
                RemediationCandidate(
                    capability=capability,
                    target=target.id,
                    action_desc=f"remediate {target.label} via {capability}",
                    available=available,
                    evidence_note=f"confidence={hypothesis.level.value}",
                )
            )
        return candidates


# Alur lengkap environment-adaptive (CANONICAL, tanpa eksekusi langsung).
# Eksekusi remediation tetap lewat AutonomousRecoveryLoop + ApprovalGate
# (lihat sam/delegated_authority/recovery.py). SAM tidak execute di sini.
