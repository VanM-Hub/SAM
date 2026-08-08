# Collaboration Proposal Engine - WP-22
# IP-3.4-003 (AO-3.4-001, paket ketiga - Distributed Governance Intelligence)
#
# Menyusun PROPOSAL kerja sama antar federation.
#
# Guardrail IP-3.4-003:
#   Collaboration != Execution (DGI-04)
#   Recommendation != Decision (DGI-03)
#   Sovereignty preserved (DGI-06)
#
# Proposal = usulan. BUKAN persetujuan, BUKAN binding, BUKAN eksekusi.
# Keputusan akhir SELALU lokal di tiap federation (sovereignty first).
#
# Konsisten dengan IP-3.4-002 negotiation: proposal yang dihasilkan
# tidak pernah ter-bind (is_bound selalu False) dan tidak pernah menjadi
# agreement (is_agreement selalu False).

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class CollaborationProposal:
    """Proposal kolaborasi antar federation (read-only, tidak ter-bind)."""

    source_id: str
    target_id: str
    capability: str
    terms: Tuple[str, ...] = ()
    alternatives: Tuple[str, ...] = ()
    is_bound: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "capability": self.capability,
            "terms": list(self.terms),
            "alternatives": list(self.alternatives),
            "is_bound": self.is_bound,
        }


@dataclass(frozen=True)
class CollaborationProposalResult:
    """Hasil penyusunan proposal (tidak pernah menghasilkan agreement)."""

    source_id: str
    target_id: str
    requested_capability: str
    proposals: Tuple[CollaborationProposal, ...] = ()
    gaps: Tuple[str, ...] = ()
    is_agreement: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "requested_capability": self.requested_capability,
            "proposals": [p.as_dict() for p in self.proposals],
            "gaps": list(self.gaps),
            "is_agreement": self.is_agreement,
        }


class CollaborationProposalEngine:
    """Menyusun proposal kolaborasi (read-only).

    Dari capability yang diminta dan capability/contract target, menyusun
    opsi proposal. Jika capability tidak tersedia, menawarkan alternatif
    atau mencatat gap. Tidak pernah men-binding proposal, tidak pernah
    menghasilkan agreement.
    """

    def propose(
        self,
        source_id: str,
        target_id: str,
        requested_capability: str,
        target_capabilities: Tuple[str, ...],
        target_contracts: Tuple[str, ...],
        required_contracts: Tuple[str, ...] = (),
    ) -> CollaborationProposalResult:
        proposals: list = []
        gaps: list = []

        if requested_capability in target_capabilities:
            if required_contracts and not all(
                c in target_contracts for c in required_contracts
            ):
                missing = tuple(
                    c for c in required_contracts if c not in target_contracts)
                gaps.append("required-contract-missing:{}".format(
                    ",".join(missing)))
            else:
                proposals.append(CollaborationProposal(
                    source_id=source_id,
                    target_id=target_id,
                    capability=requested_capability,
                    is_bound=False,
                ))
        else:
            gaps.append("capability-not-available:{}".format(
                requested_capability))
            # alternatif: capability lain yang dimiliki target
            alternatives = tuple(
                cap for cap in target_capabilities if cap != requested_capability)

        if gaps and not proposals and alternatives:
            proposals.append(CollaborationProposal(
                source_id=source_id,
                target_id=target_id,
                capability=requested_capability,
                alternatives=alternatives,
                is_bound=False,
            ))

        return CollaborationProposalResult(
            source_id=source_id,
            target_id=target_id,
            requested_capability=requested_capability,
            proposals=tuple(proposals),
            gaps=tuple(sorted(set(gaps))),
            is_agreement=False,
        )
