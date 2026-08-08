# Federation Collaboration Model - WP-21
# IP-3.4-003 (AO-3.4-001, paket ketiga - Distributed Governance Intelligence)
#
# Mendeskripsikan KOLABORASI antar federation yang berdaulat.
#
# Guardrail IP-3.4-003:
#   Collaboration != Execution (DGI-04)
#   Sovereignty preserved (DGI-06)
#   Read-only (DGI-09)
#
# Kolaborasi = deskripsi hubungan kerja sama (partner, skop, kontrak yang
# dibagi, kemampuan yang dibagi, batas). BUKAN menjalankan kerja sama,
# BUKAN mengubah registry, BUKAN eksekusi.
#
# Setiap federation tetap berdaulat: kolaborasi menggambarkan hubungan,
# bukan menciptakan otoritas bersama.

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class FederationCollaboration:
    """Deskripsi kolaborasi antara dua federation (read-only DTO).

    Menyimpan metadata kerja sama yang disepakati DI LUAR sistem (oleh
    tiap federation secara lokal/berdaulat). Kolaborasi ini TIDAK memberi
    kewenangan eksekusi dan TIDAK mengubah state.
    """

    source_id: str
    target_id: str
    purpose: str
    shared_contracts: Tuple[str, ...] = ()
    shared_capabilities: Tuple[str, ...] = ()
    constraints: Tuple[str, ...] = ()
    is_execution: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "purpose": self.purpose,
            "shared_contracts": list(self.shared_contracts),
            "shared_capabilities": list(self.shared_capabilities),
            "constraints": list(self.constraints),
            "is_execution": self.is_execution,
        }


@dataclass(frozen=True)
class CollaborationStatus:
    """Status deskripsi kolaborasi (komputasi, bukan kontrol)."""

    collaboration: FederationCollaboration
    aligned: bool
    notes: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "collaboration": self.collaboration.as_dict(),
            "aligned": self.aligned,
            "notes": list(self.notes),
        }


class FederationCollaborationModel:
    """Menyusun deskripsi kolaborasi antar federation (read-only).

    Hanya menyusun metadata kolaborasi + menilai keselarasan (alignment)
    dari contract/capability yang dibagi. TIDAK ada eksekusi, TIDAK ada
    perubahan registry, TIDAK ada otoritas bersama.
    """

    def describe(
        self,
        source_id: str,
        target_id: str,
        purpose: str,
        shared_contracts: Tuple[str, ...] = (),
        shared_capabilities: Tuple[str, ...] = (),
        constraints: Tuple[str, ...] = (),
    ) -> FederationCollaboration:
        return FederationCollaboration(
            source_id=source_id,
            target_id=target_id,
            purpose=purpose,
            shared_contracts=tuple(sorted(shared_contracts)),
            shared_capabilities=tuple(sorted(shared_capabilities)),
            constraints=tuple(sorted(constraints)),
            is_execution=False,
        )

    def assess_alignment(
        self,
        collaboration: FederationCollaboration,
        local_contracts: Tuple[str, ...],
        local_capabilities: Tuple[str, ...],
    ) -> CollaborationStatus:
        """Menilai keselarasan kolaborasi dengan capability lokal.

        Kolaborasi dianggap aligned jika semua contract & capability yang
        dibagi memang dimiliki secara lokal. Penilaian, bukan kontrol.
        """
        notes: list = []
        aligned = True
        for contract in collaboration.shared_contracts:
            if contract not in local_contracts:
                aligned = False
                notes.append("contract-not-local:{}".format(contract))
        for capability in collaboration.shared_capabilities:
            if capability not in local_capabilities:
                aligned = False
                notes.append("capability-not-local:{}".format(capability))
        if not aligned:
            notes.append("alignment-requires-local-decision")
        return CollaborationStatus(
            collaboration=collaboration,
            aligned=aligned,
            notes=tuple(notes),
        )
