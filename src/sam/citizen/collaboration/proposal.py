# Collaboration Proposal Engine - WP-12
# IP-3.3-002 (AO-3.3-001 / ED-3.3-001 2nd cycle)
#
# Menyusun PROPOSAL kolaborasi secara deterministik - BUKAN eksekusi.
# Propal hanya "identifikasi kolaborasi yang cocok"; tidak pernah:
#   - membentuk kolaborasi
#   - mengaktifkan channel
#   - menjalankan capability bersama
#   - mengubah lifecycle/governance/mutation
#
# Guardrail: Proposal != Decision. Seluruh output bertanda proposal-only.

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Sequence

from sam.citizen.collaboration.models import (
    CollaborationRole,
    CollaborationSpec,
)


@dataclass(frozen=True)
class CollaborationProposal:
    """Proposal kolaborasi (immutable, proposal-only)."""

    proposal_id: str
    targets: Tuple[str, ...]            # citizen identity_id yang diajak
    reason: str
    proposed_capabilities: Tuple[str, ...]
    suggested_spec: Optional[CollaborationSpec] = None
    is_proposal: bool = True
    basis: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "targets": list(self.targets),
            "reason": self.reason,
            "proposed_capabilities": list(self.proposed_capabilities),
            "suggested_spec": self.suggested_spec.as_dict()
            if self.suggested_spec else None,
            "is_proposal": self.is_proposal,
            "basis": list(self.basis),
        }


class CollaborationProposalEngine:
    """Menyusun proposal kolaborasi deterministik antar citizen.

    Sebuah proposal dihasilkan bila:
      - origin & target keduanya terdaftar (via registry lookup)
      - ada capability yang KOMPLEMENTER (origin butuh, target punya / sebaliknya)
      - target bukan origin (no self-collaboration)
    Proposals diurutkan secara deterministik (by target, by capability).
    """

    def __init__(self, registry):
        self._registry = registry

    def propose(self, origin_identity_id: str,
                needed_capabilities: Sequence[str],
                registry=None, descriptors: Optional[Tuple] = None,
                channel_name: str = "default") -> Tuple[CollaborationProposal, ...]:
        """Susun proposal kolaborasi untuk `origin` berdasarkan kebutuhan.

        Murni read; tidak membentuk kolaborasi apapun.
        """
        reg = registry or self._registry
        origin_entry = reg.get(origin_identity_id)
        if origin_entry is None:
            return ()

        targets = reg.all()
        proposals = []
        for target in targets:
            if target.identity_id == origin_identity_id:
                continue
            # capability target yang relevan dgn kebutuhan origin
            caps = self._capabilities_of(target.identity_id, descriptors)
            shared = tuple(c for c in needed_capabilities if c in caps)
            if not shared:
                continue
            roles = (CollaborationRole(origin_identity_id, "initiator"),
                     CollaborationRole(target.identity_id, "participant"))
            spec = CollaborationSpec.new(roles, channel_name=channel_name,
                                         shared_capabilities=shared)
            proposals.append(CollaborationProposal(
                proposal_id="prop-" + spec.collaboration_id,
                targets=(target.identity_id,),
                reason="capability complementarity: needs {!s}".format(
                    ", ".join(shared)),
                proposed_capabilities=shared,
                suggested_spec=spec,
                is_proposal=True,
                basis=("proposal only", "explicit",
                       "registry-based discovery"),
            ))

        # urutkan deterministik
        proposals.sort(key=lambda p: (p.targets, p.proposal_id))
        return tuple(proposals)

    def _capabilities_of(self, identity_id: str,
                         descriptors: Optional[Tuple]) -> Tuple[str, ...]:
        if descriptors:
            for d in descriptors:
                if getattr(d, "identity_id", None) == identity_id:
                    return tuple(getattr(d, "capabilities", ()))
        # fallback: registry entry labels -> kosong (tidak punya capability
        # yang dideklarasikan; discovery tetap registry-based).
        return ()
