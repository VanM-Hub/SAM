# Collaboration & Compatibility & Certification Workspace - IP-3.5-003
# WP-19 (Collaboration) + WP-20 (Compatibility) + WP-21 (Certification).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail: Collaboration Workspace != Collaboration Execution; Compatibility
#   adalah penilaian deklaratif (bukan negociasi); Certification adalah
#   presentasi status (bukan penerbitan sertifikat).

"""Collaboration, Compatibility & Certification Workspace.

Menyajikan pandangan kolaborasi antar-citizen, kompatibilitas capability, dan
status sertifikasi - semua deklaratif & read-only. Platform tidak memulai
kolaborasi, tidak menjalankan negosiasi, tidak menerbitkan sertifikat.
"""

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple


# --- Collaboration (WP-19) ---------------------------------------------------

@dataclass(frozen=True)
class CollaborationInput:
    """Data kolaborasi yang DIBERIKAN ke platform untuk penyajian.

    Mencerminkan keadaan kolaborasi antar-citizen (proposal/kesepakatan).
    Platform tidak memulai/menyetujui kolaborasi.
    """

    collaboration_id: str
    name: str = ""
    status: str = "unknown"  # mis. "proposed", "active", "complete"
    parties: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CollaborationWorkspaceView:
    """Pandangan kolaborasi (immutable)."""

    collaborations: Tuple[CollaborationInput, ...] = ()

    def collaboration(self, cid: str) -> Optional[CollaborationInput]:
        for c in self.collaborations:
            if c.collaboration_id == cid:
                return c
        return None

    def count(self) -> int:
        return len(self.collaborations)


# --- Compatibility (WP-20) ---------------------------------------------------

@dataclass(frozen=True)
class CompatibilityAssessment:
    """Penilaian kompatibilitas capability (deklaratif).

    Hasil perbandingan capability source vs target. Penilaian, bukan command.
    """

    source_citizen: str = ""
    target_citizen: str = ""
    compatible: bool = False
    rationale: str = ""

    @property
    def verdict(self) -> str:
        return "compatible" if self.compatible else "incompatible"


def assess_compatibility(
    source_citizen: str,
    target_citizen: str,
    source_capabilities: Sequence[str],
    target_capabilities: Sequence[str],
    required: Sequence[str] = (),
) -> CompatibilityAssessment:
    """Nilai kompatibilitas: target punya semua requirement yang diminta.

    Deterministik. Murni penilaian tampilan; tidak ada negosiasi/eksekusi.
    """
    target_set = set(target_capabilities)
    needs = tuple(required) if required else tuple(source_capabilities)
    missing = [c for c in needs if c not in target_set]
    return CompatibilityAssessment(
        source_citizen=source_citizen,
        target_citizen=target_citizen,
        compatible=not missing,
        rationale=("semua requirement terpenuhi"
                   if not missing else "kurang: %s" % ", ".join(missing)),
    )


# --- Certification (WP-21) ---------------------------------------------------

@dataclass(frozen=True)
class CertificationStatus:
    """Status sertifikasi citizen (presentational).

    Menyajikan hasil sertifikasi; platform tidak menerbitkan/mencabut.
    """

    certification_id: str = ""
    target: str = ""
    certified: bool = False
    criteria: Tuple[str, ...] = ()

    @property
    def verdict(self) -> str:
        return "certified" if self.certified else "not-certified"


@dataclass(frozen=True)
class CertificationWorkspaceView:
    """Pandangan sertifikasi (immutable)."""

    certifications: Tuple[CertificationStatus, ...] = ()

    def count(self) -> int:
        return len(self.certifications)

    def certified_count(self) -> int:
        return sum(1 for c in self.certifications if c.certified)


def build_certification_view(
    certifications: Sequence[CertificationStatus],
) -> CertificationWorkspaceView:
    """Build sertification view, deterministik."""
    return CertificationWorkspaceView(certifications=tuple(sorted(
        certifications, key=lambda c: c.certification_id)))
