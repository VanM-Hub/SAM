# Environment Recommendation Adapter - R1-005
#
# Adapter yang membuat implementation environment RECOMMENDATION (action yang
# layak dipertimbangkan atas DIAGNOSIS yang SUDAH diproduksi R1-004) memenuhi
# kontrak recommendation (ward.capability.contracts.RecommendationTarget /
# RecommendationResult) yang dimiliki SAM (M13-007).
#
# PENTING (boundary R1-005, dikunci Van 2026-08-16 rev.2):
#   - MURNI read-only. BUKAN recovery engine, BUKAN executor, BUKAN approval.
#   - Menerima DiagnosisResult (R1-004) - BUKAN findings mentah, BUKAN Dict,
#     BUKAN investigation ulang.
#   - TIDAK import `environment`, connector, AI, WardGovernor, atau executor.
#   - Action mutation HANYA bila ada CANONICAL ACTION MAPPING yang TERBUKTI
#     (dideklarasikan di sumber canonical yang auditable). TIDAK ada
#     `_derive_action` / keyword heuristic (disk->cleanup, process->restore).
#     Pemetaan heuristic = inference baru tanpa canonical mapping = DILARANG.
#   - verdict tidak otomatis -> action:
#       insufficient -> recommendations=[] (jujur)
#       candidate    -> recommendations=[] (belum cukup yakin utk mutation)
#       causal + mapping TERBUKTI -> rekomendasi action abstract dari mapping
#       causal + mapping ABSENT   -> recommendations=[] + gap dilaporkan sbg
#                                    input R1-006 (JANGAN mengarang mapping)
#   - diagnosis_ref = reference ke hasil diagnosis (dari DiagnosisResult.
#     evidence_ref sbg source-ref traceability), BUKAN salinan evidence.
#   - Read-only: TIDAK mutation, TIDAK side effect. STOP di Recommendation.
from __future__ import annotations

import hashlib
from typing import Dict, List, Optional

from sam.ward.capability.contracts import (
    DiagnosisResult,
    Recommendation,
    RecommendationResult,
    RecommendationTarget,
    SubjectRef,
)


class EnvironmentRecommendationAdapter(RecommendationTarget):
    """RecommendationTarget untuk environment mesin lokal (read-only).

    Alur:
      1. Terima DiagnosisResult (R1-004).
      2. Bila verdict insufficient/candidate -> recommendations=[] (jujur).
      3. Bila verdict causal -> hanya bila ada CANONICAL ACTION MAPPING yang
         TERBUKTI (di-inject / dari sumber canonical auditable). TIDAK ada
         mapping heuristic. Bila mapping ABSENT -> recommendations=[].
      4. Wrap jadi RecommendationResult.

    Adapter HANYA MEMBACA canonical action mapping yang sudah dideklarasikan;
    TIDAK mengarang. Sumber canonical action mapping saat ini BELUM ada
    (audit+definisi = R1-006), sehingga verdict causal -> recommendations=[]
    dengan gap jujur, BUKAN mengarang restore/protect/cleanup.
    """

    def __init__(self, subject: SubjectRef,
                 canonical_action_map: Optional[Dict[str, str]] = None) -> None:
        """Injeksi canonical action mapping.

        canonical_action_map: {finding_label_kausal: action_abstract}, sumber
        CANONICAL yang auditable (R1-006 yang mendefinisikan). Nilai default
        None = mapping ABSENT (tidak ada -> causal menghasilkan [] jujur).
        Ini BUKAN heuristic adapter; ini titik DI MANA map canonical di-deklarasi.
        """
        self._subject = subject
        # Simpan mapping SEBAGAI REFERENCE canonical (auditable), bukan dibuat
        # di sini. Bila None -> tidak ada mapping -> fail-closed [] utk causal.
        self._canonical_action_map = dict(canonical_action_map or {})

    def recommend(self, *, diagnosis: Optional[DiagnosisResult] = None,
                  capability: str = "recommend") -> RecommendationResult:
        """Rekomendasi canonical atas DiagnosisResult (read-only).

        PRINSIP: Recommend != selalu menghasilkan action. fail-closed jujur.
        """
        diagnosis = diagnosis or DiagnosisResult(
            subject=self._subject, verdict="insufficient", diagnosis=[],
            confidence=0.0, evidence_ref="tidak ada diagnosis", summary="",
            error="",
        )
        verdict = diagnosis.verdict

        # diagnosis_ref = reference hasil diagnosis (source-ref traceability).
        diagnosis_ref = diagnosis.evidence_ref or (
            "diagnosis verdict={}".format(verdict))

        # --- insufficient -> [] jujur ---
        if verdict == "insufficient":
            return RecommendationResult(
                subject=self._subject,
                diagnosis_ref=diagnosis_ref,
                recommendations=[],
                summary=(
                    "Diagnosis insufficient - belum ada tindakan yang layak "
                    "direkomendasikan dari evidence saat ini. Tidak mengarang "
                    "recovery action."
                ),
                error="",
            )

        # --- candidate -> [] utk mutation (belum cukup yakin) ---
        if verdict == "candidate":
            return RecommendationResult(
                subject=self._subject,
                diagnosis_ref=diagnosis_ref,
                recommendations=[],
                summary=(
                    "Verdict candidate - belum cukup yakin untuk merekomendasikan "
                    "tindakan mutation. Tidak merekomendasikan mutation dari "
                    "kandidat yang belum kuat."
                ),
                error="",
            )

        # --- causal ---
        if verdict == "causal":
            # HANYA rekomendasi bila ada canonical action mapping TERBUKTI.
            findings = list(diagnosis.diagnosis or [])
            recs: List[Recommendation] = []
            used_for = []  # finding label yang TERSEDIA mapping canonical
            for finding in findings:
                action = self._canonical_action_map.get(finding.label)
                if action is None:
                    # finding kausal ini TIDAK punya canonical mapping -> TIDAK
                    # mengarang; lewati (bukan dikonversi heuristic).
                    continue
                used_for.append(finding.label)
                recs.append(
                    Recommendation(
                        recommendation_id=_stable_rec_id(
                            self._subject.subject_id, finding.label),
                        subject_id=self._subject.subject_id,
                        action=action,               # abstract dari canonical mapping
                        target=finding.label,         # entitas target abstract
                        rationale=(
                            "berbasis finding causal '{}' dari diagnosis {} "
                            "(lineage diagnosis_ref) dengan confidence {:.2f} "
                            "- action dari canonical action mapping."
                        ).format(finding.label, verdict, finding.confidence),
                        approval_required=True,
                    )
                )

            if not recs:
                return RecommendationResult(
                    subject=self._subject,
                    diagnosis_ref=diagnosis_ref,
                    recommendations=[],
                    summary=(
                        "Diagnosis tersedia (verdict causal), tetapi belum ada "
                        "canonical action mapping yang dapat dibuktikan untuk "
                        "merekomendasikan tindakan mutation. Tidak mengarang "
                        "restore/protect/cleanup. Gap ini menjadi input R1-006 "
                        "(definisi canonical action mapping SEBELUM eksekusi)."
                    ),
                    error="",
                )

            return RecommendationResult(
                subject=self._subject,
                diagnosis_ref=diagnosis_ref,
                recommendations=recs,
                summary=(
                    "{} finding causal termapping canonical action mapping; "
                    "{} rekomendasi mutation disusun dari mapping TERBUKTI."
                ).format(len(used_for), len(recs)),
                error="",
            )

        # --- verdict tidak dikenal -> [] jujur (fail-closed) ---
        return RecommendationResult(
            subject=self._subject,
            diagnosis_ref=diagnosis_ref,
            recommendations=[],
            summary="Verdict diagnosis tidak dikenal - rekomendasi kosong (fail-closed).",
            error="",
        )


def _stable_rec_id(subject_id: str, label: str) -> str:
    raw = "{}|{}".format(subject_id, label).encode("utf-8")
    return "rec-" + hashlib.sha256(raw).hexdigest()[:12]
