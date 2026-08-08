# Federation Trust Explainability - WP-16
# IP-3.4-002 (AO-3.4-001 / ED-3.4-001, paket kedua)
#
# Menjelaskan trust & interoperability:
#   - mengapa trust tinggi/rendah
#   - evidence apa yang digunakan
#   - capability apa yang tidak kompatibel
#   - rekomendasi peningkatan interoperability
#
# Guardrail IP-3.4-002:
#   Evidence-first - seluruh penjelasan berbasis bukti
#   Recommendation != Authority - rekomendasi tidak memaksa
#
# Penjelasan = read-only. Tidak mengubah trust, tidak menjalankan aksi.

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from sam.citizen.federation.trust import (
    FederationTrustProfile,
    TrustEvidence,
)


@dataclass(frozen=True)
class TrustExplanation:
    """Penjelasan trust satu member (evidence-based)."""

    member_id: str
    summary: str
    reasons: Tuple[str, ...] = ()
    evidence: Tuple[TrustEvidence, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "member_id": self.member_id,
            "summary": self.summary,
            "reasons": list(self.reasons),
            "evidence": [e.as_dict() for e in self.evidence],
        }


@dataclass(frozen=True)
class InteropExplanation:
    """Penjelasan interoperability + rekomendasi peningkatan."""

    source_id: str
    target_id: str
    summary: str
    gaps: Tuple[str, ...] = ()
    recommendations: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "summary": self.summary,
            "gaps": list(self.gaps),
            "recommendations": list(self.recommendations),
        }


class TrustExplainer:
    """Penyusun penjelasan trust (read-only, evidence-first)."""

    def explain_profile(self, profile: FederationTrustProfile) -> TrustExplanation:
        level = profile.level.level
        if level == "unknown":
            summary = ("Trust {} belum dapat dinilai: belum ada bukti.".format(
                profile.member_id))
        elif level == "high":
            summary = ("Trust {} tinggi: didukung bukti certification, "
                       "compatibility, contract, dan/atau health.".format(
                           profile.member_id))
        elif level == "medium":
            summary = ("Trust {} sedang: bukti positif ada tapi belum penuh.".format(
                profile.member_id))
        else:
            summary = ("Trust {} rendah: bukti kurang atau ada kendala.".format(
                profile.member_id))

        reasons: list = []
        if not profile.evidence:
            reasons.append("tidak-ada-evidence")
        for e in profile.evidence:
            reasons.append("evidence-{}:{}".format(e.kind, e.source))
        for c in profile.constraints:
            reasons.append("constraint:{}".format(c.name))

        return TrustExplanation(
            member_id=profile.member_id,
            summary=summary,
            reasons=tuple(reasons),
            evidence=profile.evidence,
        )

    def explain_interoperability(
        self,
        source_id: str,
        target_id: str,
        compatible: bool,
        gaps: Tuple[str, ...],
        recommended: Tuple[str, ...],
    ) -> InteropExplanation:
        if compatible:
            summary = ("{} dan {} dapat bekerja sama (kompatibel) "
                       "berdasarkan kontrak/capability yang dibagi.".format(
                           source_id, target_id))
        else:
            summary = ("{} dan {} belum kompatibel: ada gap yang menghalangi "
                       "interoperability.".format(source_id, target_id))
        return InteropExplanation(
            source_id=source_id,
            target_id=target_id,
            summary=summary,
            gaps=tuple(sorted(gaps)),
            recommendations=tuple(sorted(recommended)),
        )
