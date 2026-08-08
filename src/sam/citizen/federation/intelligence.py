# Federation Intelligence Engine - WP-25
# IP-3.4-003 (AO-3.4-001, paket ketiga - Distributed Governance Intelligence)
#
# Reasoning LINTAS federation - tiap federation reasoning secara lokal,
# hasil reasoning dipertukarkan sebagai EVIDENCE (bukan authority), lalu
# diagregasi secara deterministik.
#
# Guardrail IP-3.4-003:
#   Federation Intelligence != Central Intelligence (DGI-05)
#   Deterministic reasoning (DGI-07)
#   Evidence-first (DGI-08)
#   Read-only (DGI-09)
#
# BUKAN Distributed Governance & BUKAN Shared Governance. Setiap federation
# TETAP melakukan reasoning secara lokal; intelligence engine hanya
# mengagregasi output reasoning lokal yang sudah menjadi evidence, tanpa
# menggabungkan otoritas.
#
# Output = penilaian teragregasi (assessment), bukan keputusan. Keputusan
# tetap lokal. Deterministik: tanpa RNG, tanpa waktu, agregasi murni.

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from sam.citizen.federation.evidence_exchange import EvidenceGraph


@dataclass(frozen=True)
class LocalReasoning:
    """Hasil reasoning satu federation (evidence, bukan authority)."""

    member_id: str
    assessment: str        # mis. "audit-clean", "risk-high", "compliant"
    confidence: float      # 0.0..1.0
    reasons: Tuple[str, ...] = ()
    trusted: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "member_id": self.member_id,
            "assessment": self.assessment,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "trusted": self.trusted,
        }


@dataclass(frozen=True)
class FederationInsight:
    """Penilaian reasoning teragregasi lintas federation (read-only)."""

    focus: str
    agreement_score: float   # 0.0..1.0 seberapa sepakat anggota
    signal: str              # clear | mixed | inconclusive
    members: Tuple[LocalReasoning, ...] = ()
    notes: Tuple[str, ...] = ()
    is_decision: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "focus": self.focus,
            "agreement_score": self.agreement_score,
            "signal": self.signal,
            "members": [m.as_dict() for m in self.members],
            "notes": list(self.notes),
            "is_decision": self.is_decision,
        }


class FederationIntelligenceEngine:
    """Agregasi reasoning lokal lintas federation (read-only, deterministik).

    Menggabungkan (bukan menyatukan otoritas) hasil reasoning lokal tiap
    federation. Skor kesepakatan dihitung dari kepercayaan & keyakinan tiap
    anggota secara deterministik. is_decision selalu False - insight bukan
    keputusan; keputusan tetap lokal per federation.
    """

    def aggregate(
        self,
        focus: str,
        local_reasonings: Tuple[LocalReasoning, ...],
    ) -> FederationInsight:
        if not local_reasonings:
            return FederationInsight(
                focus=focus,
                agreement_score=0.0,
                signal="inconclusive",
                members=(),
                is_decision=False,
            )

        # deterministik: rata-rata keyakinan tertimbang dari anggota trusted
        total_weight = 0.0
        weighted = 0.0
        for reason in local_reasonings:
            weight = reason.confidence
            total_weight += weight
            weighted += weight * (1.0 if reason.trusted else 0.0)

        agreement = weighted / total_weight if total_weight > 0 else 0.0
        agreement = max(0.0, min(1.0, agreement))

        if agreement >= 0.7:
            signal = "clear"
        elif agreement >= 0.4:
            signal = "mixed"
        else:
            signal = "inconclusive"

        notes = ("insight-is-assessment-not-decision",) if agreement >= 0.7 else ()

        return FederationInsight(
            focus=focus,
            agreement_score=agreement,
            signal=signal,
            members=tuple(sorted(
                local_reasonings, key=lambda r: r.member_id)),
            notes=notes,
            is_decision=False,
        )

    def incorporate_evidence_graph(
        self,
        graph: EvidenceGraph,
    ) -> Tuple[str, ...]:
        """Mengambil observasi dari evidence graph sebagai bahan reasoning.

        Evidence graph diterima sebagai bukti; tidak ada sinkronisasi state,
        tidak ada eksekusi. Mengembalikan label observasi yang tersedia.
        """
        return tuple(
            "{node_id}:{kind}".format(node_id=n.node_id, kind=n.kind)
            for n in graph.nodes if n.kind == "observation")
