# Citizen API - IP-3.5-003 (AO-ENG-001, MISSION-3.5)
# WP-22: facade read/assemble-only untuk Citizen & Federation Experience.
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail (IP-3.5): CitizenAPI bersifat READ/PREPARE/PRESENT only.
#   TIDAK ada: citizen modification, federation mutation, collaboration
#   start, negotiation, certification issue/certify, operational action call.
#   CitizenAPI PRESENTS citizen/federation; never runs citizen action.

"""Citizen & Federation API (Facade).

Facade read-only untuk Citizen Experience. Menerima data citizen, federation,
kolaborasi, kompatibilitas, dan sertifikasi dari luar (governed capability
API / caller), menyusun pandangan terpadu, dan menyajikannya. Tidak
memodifikasi citizens atau federation runtime.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

from sam.platform.citizen_workspace import (
    CitizenInput,
    FederationInput,
    FederationMemberInput,
    CitizenWorkspaceView,
    FederationWorkspaceView,
    build_citizen_view,
    build_federation_view,
)
from sam.platform.collaboration_workspace import (
    CollaborationInput,
    CollaborationWorkspaceView,
    CompatibilityAssessment,
    CertificationStatus,
    CertificationWorkspaceView,
    assess_compatibility,
    build_certification_view,
)


@dataclass(frozen=True)
class CitizenSnapshot:
    """Snapshot baca-saja Citizen Experience untuk disajikan.

    Menyajikan keadaan citizen+federation; tidak memegang otoritas eksekusi.
    """

    citizens: Tuple[CitizenInput, ...] = ()
    federations: Tuple[FederationInput, ...] = ()
    collaborations: Tuple[CollaborationInput, ...] = ()
    certifications: Tuple[CertificationStatus, ...] = ()

    @property
    def citizen_count(self) -> int:
        return len(self.citizens)

    @property
    def federation_count(self) -> int:
        return len(self.federations)


class CitizenExperienceAPI:
    """Facade read-only untuk Citizen & Federation Experience.

    Menerima data citizen/federation dari luar, menyusun pandangan terpadu,
    dan menyajikannya untuk presentation layer. DILARANG memodifikasi
    citizens / federation / menjalankan aksi citizen.
    """

    def __init__(self) -> None:
        self._citizens: Dict[str, CitizenInput] = {}
        self._federations: Dict[str, FederationInput] = {}
        self._collaborations: Dict[str, CollaborationInput] = {}
        self._certifications: Dict[str, CertificationStatus] = {}

    # --- Input (diberikan dari luar) ----------------------------------------

    def register_citizen(self, citizen: CitizenInput) -> None:
        self._citizens[citizen.identity_id] = citizen

    def register_federation(self, federation: FederationInput) -> None:
        self._federations[federation.federation_id] = federation

    def register_collaboration(self, collab: CollaborationInput) -> None:
        self._collaborations[collab.collaboration_id] = collab

    def register_certification(self, cert: CertificationStatus) -> None:
        self._certifications[cert.certification_id] = cert

    # --- Assembly (read-only) -----------------------------------------------

    def snapshot(self) -> CitizenSnapshot:
        """Snapshot Citizen Experience terpadu (deterministik)."""
        return CitizenSnapshot(
            citizens=tuple(sorted(self._citizens.values(),
                                  key=lambda c: c.identity_id)),
            federations=tuple(sorted(self._federations.values(),
                                     key=lambda f: f.federation_id)),
            collaborations=tuple(sorted(self._collaborations.values(),
                                        key=lambda c: c.collaboration_id)),
            certifications=tuple(sorted(self._certifications.values(),
                                        key=lambda c: c.certification_id)),
        )

    def citizen_view(self) -> CitizenWorkspaceView:
        return build_citizen_view(self._citizens.values())

    def federation_view(self) -> FederationWorkspaceView:
        return build_federation_view(self._federations.values())

    def collaboration_view(self) -> CollaborationWorkspaceView:
        return CollaborationWorkspaceView(collaborations=tuple(sorted(
            self._collaborations.values(), key=lambda c: c.collaboration_id)))

    def certification_view(self) -> CertificationWorkspaceView:
        return build_certification_view(self._certifications.values())

    def compat(self, source: str, target: str, required: Sequence[str] = (),
               capabilities: Optional[Dict[str, Tuple[str, ...]]] = None
               ) -> CompatibilityAssessment:
        """Nilai kompatibilitas capability antar-citizen (penilaian).

        Menggunakan capability yang didaftarkan (jika tersedia) atau kosong.
        Murni penilaian deklaratif.
        """
        c = capabilities or {i: c.capabilities for i, c in self._citizens.items()}
        src_caps = tuple(c.get(source, ()))
        tgt_caps = tuple(c.get(target, ()))
        return assess_compatibility(source, target, src_caps, tgt_caps, required)

    def count_citizens(self) -> int:
        return len(self._citizens)

    def count_federations(self) -> int:
        return len(self._federations)
