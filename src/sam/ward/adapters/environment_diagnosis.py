# Environment Diagnosis Adapter - R1-004
#
# Adapter yang membuat implementation environment DIAGNOSIS (verdict jujur
# atas evidence yang SUDAH diproduksi investigasi R1-003) memenuhi kontrak
# diagnosis (ward.capability.contracts.DiagnosisTarget / DiagnosisResult)
# yang dimiliki SAM (M13-006).
#
# PENTING (boundary R1-004, dikunci Van 2026-08-16):
#   - MURNI evaluator read-only. BUKAN engine diagnosis baru.
#   - Menerima SELECTED EVIDENCE (List[Dict]) dari InvestigationResult.findings,
#     BUKAN findings mentah, BUKAN investigation ulang.
#   - TIDAK import `environment`: tidak discovery, tidak DiagnosisEngine,
#     tidak scoring engine. Sinyal kausal dibawa evidence (field `causal`),
#     bukan daftar source hardcoded.
#   - REUSE ConfidenceAssessor untuk confidence evidence (TIDAK hitung ulang),
#     dan Finding canonical (M13-006) untuk diagnosis output.
#   - confidence EVIDENCE TERPISAH dari verdict (diagnostic sufficiency):
#     confidence TIDAK dipaksa 0.0 saat verdict `insufficient`.
#   - Read-only: TIDAK mutation, TIDAK recovery, TIDAK recommendation, TIDAK
#     mengarang sebab. Evidence tidak cukup -> INSUFFICIENT jujur.
#   - "candidate" (R1-003) TIDAK dinaikkan jadi "causal" hanya karena nama
#     terdengar masuk akal; hubungan kausal harus dibawa evidence.
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from sam.ward.capability.contracts import (
    DiagnosisResult,
    DiagnosisTarget,
    Finding,
    SubjectRef,
)


class EnvironmentDiagnosisAdapter(DiagnosisTarget):
    """DiagnosisTarget untuk environment mesin lokal (read-only evaluator).

    Alur:
      1. Terima SELECTED EVIDENCE (List[Dict]) dari investigasi R1-003.
         Setiap entry = {source, statement, strength, negative, causal}.
      2. Hitung EVIDENCE confidence (reuse ConfidenceAssessor) - TIDAK
         dipaksakan ke 0 pada verdict insufficient.
      3. Pilih evidence yang membawa sinyal kausal (causal == True). Ini
         lapisan label jujur, BUKAN reasoning engine baru: SAM hanya membaca
         atribut `causal` yang dideklarasikan di sumber observable.
      4. Bila TIDAK ada evidence kausal -> verdict `insufficient` (diagnosis=[],
         tapi confidence TETAP nilai evidence - terpisah).
      5. Bila ada evidence kausal -> klasifikasi:
           strength >= 0.7 -> verdict `causal` (kondisi kausal kuat)
           strength <  0.7 -> verdict `candidate` (indikasi kausal lemah)
         diagnosis berisi Finding canonical untuk tiap evidence kausal.
      6. Wrap jadi DiagnosisResult.

    Adapter HANYA menilai; TIDAK mencari bukti baru (itu = investigation ulang,
    dilarang R1-004).
    """

    def __init__(self, subject: SubjectRef) -> None:
        self._subject = subject

    def diagnose(self, *, evidence: List[Dict[str, Any]] = None,
                 capability: str = "diagnose") -> DiagnosisResult:
        """Diagnosis verdict jujur atas selected evidence dari investigasi."""
        evidence = list(evidence or [])

        # 2. evidence confidence (observasi) - TERPISAH dari sufficiency.
        conf = self._evidence_confidence(evidence)

        if not evidence:
            return DiagnosisResult(
                subject=self._subject,
                verdict="insufficient",
                diagnosis=[],
                confidence=conf,
                evidence_ref="tidak ada evidence untuk didiagnosis",
                summary="tidak ada evidence untuk didiagnosis - tidak mengarang "
                        "temuan atau sebab.",
                error="",
            )

        # 3. pilih sinyal kausal yang dibawa evidence.
        causal = [e for e in evidence if e.get("causal")]
        if not causal:
            return DiagnosisResult(
                subject=self._subject,
                verdict="insufficient",
                diagnosis=[],
                confidence=conf,
                evidence_ref=self._evidence_ref(evidence),
                summary=("{} evidence anomali (confidence {:.2f}), tetapi TIDAK "
                         "ada hubungan kausal yang dibawa evidence -> "
                         "INSUFFICIENT. Ini bukan pernyataan 'X bukan penyebab'; "
                         "evidence saat ini belum cukup untuk menentukan sebab.")
                         .format(len(evidence), conf),
                error="",
            )

        # 4-5. klasifikasi verdict sesuai kekuatan sinyal kausal.
        strong = [e for e in causal if float(e.get("strength", 0.0)) >= 0.7]
        verdict = "causal" if strong else "candidate"
        diag = [self._to_finding(e, conf) for e in causal]

        return DiagnosisResult(
            subject=self._subject,
            verdict=verdict,
            diagnosis=diag,
            confidence=conf,
            evidence_ref=self._evidence_ref(evidence),
            summary=self._summary(verdict, causal),
            error="",
        )

    # --- pembantu (jujur, deterministik) ---

    def _to_finding(self, ev: Dict[str, Any], conf: float) -> Finding:
        """Bangun Finding canonical (M13-006) dari satu evidence kausal."""
        return Finding(
            finding_id=_stable_id(self._subject.subject_id, str(ev.get("statement", ""))),
            subject_id=self._subject.subject_id,
            label=str(ev.get("statement", "")),
            evidence=ev,
            confidence=conf,
        )

    @staticmethod
    def _evidence_confidence(evidence: List[Dict[str, Any]]) -> float:
        """REUSE ConfidenceAssessor - confidence bahwa EVIDENCE nyata.

        Membangun ulang objek Evidence dari dict (source/statement/strength/
        negative/causal). TIDAK memanggil engine/observable; hanya assessor.
        """
        if not evidence:
            return 0.0
        try:
            from sam.environment.confidence import ConfidenceAssessor, Evidence
            return round(float(ConfidenceAssessor().confidence_score(
                [Evidence(
                    source=str(e.get("source", "")),
                    statement=str(e.get("statement", "")),
                    strength=float(e.get("strength", 1.0)),
                    negative=bool(e.get("negative", False)),
                    causal=bool(e.get("causal", False)),
                ) for e in evidence]
            )), 2)
        except Exception:  # pragma: no cover - defensif
            return 0.0

    @staticmethod
    def _evidence_ref(evidence: List[Dict[str, Any]]) -> str:
        """Referensi ringkas ke evidence (traceability, tanpa raw/secret)."""
        if not evidence:
            return "tidak ada evidence"
        sources = sorted({str(e.get("source", "?")) for e in evidence})
        return "diagnosis evidence sources={}; n={}".format(
            ",".join(sources), len(evidence))

    @staticmethod
    def _summary(verdict: str, causal: List[Dict[str, Any]]) -> str:
        if verdict == "causal":
            return ("Ada {} evidence yang membawa hubungan kausal; SAM "
                    "menyatakan verdict causal (sebab dapat dinilai dari "
                    "evidence, TIDAK mengarang).").format(len(causal))
        return ("Ada {} indikasi kausal dari evidence, tetapi kekuatannya "
                "belum cukup untuk menyatakan sebab -> verdict candidate "
                "(memerlukan evidence kausal lebih kuat).").format(len(causal))


def _stable_id(subject_id: str, statement: str) -> str:
    raw = "{}|{}".format(subject_id, statement).encode("utf-8")
    return "diag-" + hashlib.sha256(raw).hexdigest()[:12]
