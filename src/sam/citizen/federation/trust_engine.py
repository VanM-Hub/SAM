# Federation Trust Evaluation Engine - WP-12
# IP-3.4-002 (AO-3.4-001 / ED-3.4-001, paket kedua)
#
# Evaluasi trust secara DETERMINISTIK berdasarkan bukti:
#   certification, compatibility, contract, health, evidence.
#
# Guardrail IP-3.4-002:
#   Trust != Authority      - hasil evaluasi bukan kewenangan
#   Evidence-first          - seluruh trust dapat dijelaskan
#   Deterministic           - input identik -> output identik
#   Assessment != Control   - penilaian tidak mengendalikan Federation
#
# TIDAK ada pembelajaran adaptif, TIDAK ada AI, TIDAK ada model statistik
# yang berubah. Semua aturan tetap & deterministik.

from typing import Any, Dict, Optional, Tuple

from sam.citizen.federation.trust import (
    FederationTrustProfile,
    TrustConstraint,
    TrustEvidence,
    TrustLevel,
    _trust_rank,
)

# bobot bukti (deterministik, tetap)
_WEIGHT = {
    "certification": 0.30,
    "compatibility": 0.25,
    "contract": 0.20,
    "health": 0.15,
    "evidence": 0.10,
}


def _evidence_score(evidence: Tuple[TrustEvidence, ...]) -> float:
    """Skor agregat bukti (0..1) berdasarkan jenis bukti yang hadir.

    Jenis bukti yang hadir memberi bobot penuh; bukti tambahan pada jenis
    yang sama menambah bobot (maks 2x bobot jenis tsb) - deterministik.
    """
    if not evidence:
        return 0.0
    present = {e.kind for e in evidence}
    score = 0.0
    for kind, weight in _WEIGHT.items():
        if kind in present:
            count = sum(1 for e in evidence if e.kind == kind)
            # bukti pertama bobot penuh; tambahan mendekati 2x bobot
            bonus = min(weight, (count - 1) * 0.1)
            score += weight + bonus
    return min(1.0, score)


def _constraint_penalty(constraints: Tuple[TrustConstraint, ...]) -> float:
    """Penalti kendala (0..~0.5)."""
    if not constraints:
        return 0.0
    return min(0.5, len(constraints) * 0.15)


def _quality_penalty(
    certification: Optional[str],
    compatibility: Optional[str],
    health: Optional[str],
) -> float:
    """Penalti kualitas sinyal sub-optimal (deterministik).

    Semakin rendah kualitas certification/compatibility/health, semakin
    besar penalti terhadap bobot jenisnya (evidence-first: trust mengikuti
    kualitas bukti, bukan hanya kehadirannya).
    """
    penalty = 0.0
    cert = (certification or "").strip().lower()
    if cert and cert not in ("certified", "capable"):
        penalty += _WEIGHT["certification"] * 0.5
    compat = (compatibility or "").strip().lower()
    if compat and compat != "compatible":
        penalty += _WEIGHT["compatibility"] * (0.6 if compat == "incompatible" else 0.4)
    h = (health or "").strip().lower()
    if h and h != "healthy":
        penalty += _WEIGHT["health"] * (0.8 if h == "unavailable" else 0.5)
    return penalty


def _level_from_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    if score > 0.0:
        return "low"
    return "unknown"


def _signals_to_evidence(
    certification: Optional[str],
    compatibility: Optional[str],
    contract: Tuple[str, ...],
    health: Optional[str],
) -> Tuple[TrustEvidence, ...]:
    ev: list = []
    if certification:
        ev.append(TrustEvidence("certification", "certification",
                                "level={}".format(certification)))
    if compatibility:
        ev.append(TrustEvidence("compatibility", "compatibility",
                                "level={}".format(compatibility)))
    for c in contract:
        ev.append(TrustEvidence("contract", "contract", "contract={}".format(c)))
    if health:
        ev.append(TrustEvidence("health", "health", "state={}".format(health)))
    return tuple(ev)


class TrustEvaluationEngine:
    """Engine evaluasi trust member Federation (deterministik, evidence-first)."""

    def evaluate(
        self,
        member_id: str,
        certification: Optional[str] = None,
        compatibility: Optional[str] = None,
        contract: Tuple[str, ...] = (),
        health: Optional[str] = None,
        explicit_evidence: Tuple[TrustEvidence, ...] = (),
        constraints: Tuple[TrustConstraint, ...] = (),
    ) -> FederationTrustProfile:
        """Evaluasi trust berdasarkan bukti yang DIBERIKAN.

        Semua sinyal diubah ke TrustEvidence, lalu diskor deterministik.
        Hasil = FederationTrustProfile (assessment, bukan otoritas).
        """
        built = _signals_to_evidence(certification, compatibility, contract,
                                     health)
        evidence = tuple(sorted(built + tuple(explicit_evidence),
                                key=lambda e: (e.kind, e.source)))
        constraints_sorted = tuple(sorted(constraints, key=lambda c: c.name))

        score = _evidence_score(evidence)
        # kualitas sinyal ikut dinilai (deterministik): nilai sub-optimal
        # menurunkan skor sesuai bobot jenisnya
        score -= _quality_penalty(certification, compatibility, health)
        score -= _constraint_penalty(constraints_sorted)
        score = max(0.0, min(1.0, score))

        level = _level_from_score(score)
        profile = FederationTrustProfile(
            member_id=member_id,
            level=TrustLevel(level),
            evidence=evidence,
            constraints=constraints_sorted,
        )
        return profile


class TrustAggregator:
    """Agregasi trust beberapa member (read-only, deterministik)."""

    def aggregate(
        self, profiles: Tuple[FederationTrustProfile, ...]
    ) -> Dict[str, Any]:
        """Ringkasan distribusi trust kolektif."""
        if not profiles:
            return {
                "count": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "unknown": 0,
            }
        counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
        for p in profiles:
            counts[p.level.level] = counts.get(p.level.level, 0) + 1
        return {
            "count": len(profiles),
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"],
            "unknown": counts["unknown"],
        }
