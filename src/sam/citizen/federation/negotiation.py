# Federation Capability Negotiation - WP-14
# IP-3.4-002 (AO-3.4-001 / ED-3.4-001, paket kedua)
#
# Proposal negosiasi capability antar Federation Member.
#
# HANYA menghasilkan:
#   proposal
#   alternative
#   compatibility gap
#
# Guardrail IP-3.4-002:
#   Negotiation != Agreement - negosiasi menghasilkan PROPOSAL, bukan perjanjian
#   Interoperability != Execution - tidak ada activation/binding
#
# Negosiasi ini TIDAK PERNAH melakukan activation atau binding. Ia hanya
# menyusun opsi kerja sama yang MASIH HARUS disetujui secara lokal.

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class NegotiationProposal:
    """Satu opsi kerja sama (belum disetujui / tidak mengikat)."""

    capability: str
    contract: str
    source_id: str
    target_id: str
    is_bound: bool = False  # SELALU False: tidak pernah binding

    def __post_init__(self) -> None:
        # negosiasi tidak pernah menghasilkan binding otomatis
        object.__setattr__(self, "is_bound", False)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "capability": self.capability,
            "contract": self.contract,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "is_bound": self.is_bound,
        }


@dataclass(frozen=True)
class NegotiationResult:
    """Hasil negosiasi: proposal + alternative + gap (tanpa putusan)."""

    source_id: str
    target_id: str
    requested_capability: str
    proposals: Tuple[NegotiationProposal, ...] = ()
    alternatives: Tuple[NegotiationProposal, ...] = ()
    gaps: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposals",
                           tuple(sorted(self.proposals,
                                        key=lambda p: (p.capability, p.contract))))
        object.__setattr__(self, "alternatives",
                           tuple(sorted(self.alternatives,
                                        key=lambda p: (p.capability, p.contract))))
        object.__setattr__(self, "gaps", tuple(sorted(self.gaps)))

    @property
    def is_agreement(self) -> bool:
        """SELALU False: negosiasi tidak menghasilkan persetujuan."""
        return False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "requested_capability": self.requested_capability,
            "proposals": [p.as_dict() for p in self.proposals],
            "alternatives": [a.as_dict() for a in self.alternatives],
            "gaps": list(self.gaps),
            "is_agreement": self.is_agreement,
        }


class CapabilityNegotiator:
    """Menyusun proposal kerja sama (read-only, tanpa binding/activation)."""

    def negotiate(
        self,
        source_id: str,
        target_id: str,
        requested_capability: str,
        target_capabilities: Tuple[str, ...],
        target_contracts: Tuple[str, ...],
        source_contracts: Tuple[str, ...],
        shared_contracts: Tuple[str, ...],
    ) -> NegotiationResult:
        proposals: list = []
        alternatives: list = []
        gaps: list = []

        if requested_capability in target_capabilities:
            # pilih contract yang dibagi kedua pihak (jika ada)
            if shared_contracts:
                for c in shared_contracts:
                    proposals.append(NegotiationProposal(
                        requested_capability, c, source_id, target_id))
            else:
                gaps.append("no-shared-contract-for-requested")
        else:
            gaps.append("capability-not-available:{}".format(
                requested_capability))
            # alternative: capability serupa lain yang tersedia
            for cap in sorted(set(target_capabilities)
                              & set(source_contracts)):
                if cap == requested_capability:
                    continue
                alternatives.append(NegotiationProposal(
                    cap, cap, source_id, target_id))

        if not proposals and not alternatives:
            gaps.append("no-negotiable-capability")

        return NegotiationResult(
            source_id=source_id,
            target_id=target_id,
            requested_capability=requested_capability,
            proposals=tuple(proposals),
            alternatives=tuple(alternatives),
            gaps=tuple(gaps),
        )
