# Federation Interoperability Model - WP-13
# IP-3.4-002 (AO-3.4-001 / ED-3.4-001, paket kedua)
#
# Model kemampuan dua Federation untuk bekerja sama berdasarkan:
#   contract, capability, compatibility, certification.
#
# Guardrail IP-3.4-002:
#   Interoperability != Execution - kompatibilitas TIDAK memicu aksi
#   Compatibility != Approval      - approval tetap lokal
#
# InteroperabilityAssessment = HASIL PENILAIAN (read-only). Ia menyatakan
# "dua Federation dapat bekerja sama bila X", BUKAN "Federation A sekarang
# boleh menjalankan capability di Federation B".

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class InteroperabilityAssessment:
    """Penilaian interoperabilitas dua Federation Member."""

    source_id: str
    target_id: str
    compatible: bool = False
    matched_contracts: Tuple[str, ...] = ()
    matched_capabilities: Tuple[str, ...] = ()
    gaps: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "matched_contracts",
            tuple(sorted(self.matched_contracts)))
        object.__setattr__(
            self, "matched_capabilities",
            tuple(sorted(self.matched_capabilities)))
        object.__setattr__(self, "gaps", tuple(sorted(self.gaps)))

    @property
    def can_interoperate(self) -> bool:
        """Penilaian kompatibilitas. BUKAN otorisasi eksekusi."""
        return self.compatible

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "compatible": self.compatible,
            "matched_contracts": list(self.matched_contracts),
            "matched_capabilities": list(self.matched_capabilities),
            "gaps": list(self.gaps),
        }


class InteroperabilityEngine:
    """Menyimpulkan interoperabilitas dua member (read-only)."""

    def assess(
        self,
        source_id: str,
        target_id: str,
        source_contracts: Tuple[str, ...],
        target_contracts: Tuple[str, ...],
        source_capabilities: Tuple[str, ...],
        target_capabilities: Tuple[str, ...],
        source_cert: Optional[str] = None,
        target_cert: Optional[str] = None,
    ) -> InteroperabilityAssessment:
        matched_contracts = tuple(
            sorted(set(source_contracts) & set(target_contracts)))
        matched_caps = tuple(
            sorted(set(source_capabilities) & set(target_capabilities)))
        gaps = self._compute_gaps(
            source_contracts, target_contracts,
            source_capabilities, target_capabilities,
            source_cert, target_cert)
        compatible = bool(matched_contracts) or bool(matched_caps)
        return InteroperabilityAssessment(
            source_id=source_id,
            target_id=target_id,
            compatible=compatible,
            matched_contracts=matched_contracts,
            matched_capabilities=matched_caps,
            gaps=gaps,
        )

    @staticmethod
    def _compute_gaps(
        source_contracts, target_contracts,
        source_caps, target_caps,
        source_cert, target_cert,
    ) -> Tuple[str, ...]:
        gaps: list = []
        if not (set(source_contracts) & set(target_contracts)) \
                and not (set(source_caps) & set(target_caps)):
            gaps.append("no-shared-contract-or-capability")
        if source_cert and target_cert and source_cert != target_cert:
            gaps.append("certification-level-mismatch")
        return tuple(gaps)
