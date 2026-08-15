# Environment Investigation Adapter - R1-003
#
# Adapter yang membuat implementation environment INVESTIGATION canonical
# (DiagnosisEngine.investigate di atas EntityGraph yang dibangun dari
# EnvironmentDiscovery) memenuhi kontrak investigation
# (ward.capability.contracts.InvestigationTarget / InvestigationResult) yang
# SUDAH dimiliki SAM.
#
# PENTING (boundary R1-003, dikunci Van 2026-08-16):
#   - MURNI boundary/jembatan. BUKAN engine investigation baru.
#   - REUSE DiagnosisEngine.investigate() (existing canonical, M14-PROVEN).
#   - TIDAK membuat model Finding baru. Hasil = InvestigationResult.findings
#     (List[Dict]). Finding (M13-006) milik R1-004 Diagnosis - tidak dipakai
#     prematur di sini.
#   - TIDAK menambahkan fakta baru (CPU%, memory%, disk) yang BELUM diobservasi
#     discovery. Hanya menerjemahkan EntityGraph -> DiagnosisEngine, lalu
#     mengembalikan apa yang evidence nyata mendukung. Evidence tidak cukup ->
#     INSUFFICIENT jujur (0 fabrikasi, 0 root-cause claim).
#   - Read-only: TIDAK mutation, TIDAK recommendation, TIDAK recovery, TIDAK
#     import harness.
#   - Satu-satunya tempat di luar environment/ yang memanggil DiagnosisEngine.
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sam.ward.capability.contracts import (
    InvestigationResult,
    InvestigationTarget,
    SubjectRef,
)


class EnvironmentInvestigationAdapter(InvestigationTarget):
    """InvestigationTarget untuk environment mesin lokal (read-only).

    Alur (semua dari fakta observasi real):
      1. discovery.discover() -> DiscoveryScan (entitas process/port/file/env).
      2. EntityGraph.from_scan(entities) -> graph relasi.
      3. Pilih kandidat dari fakta health (proses health!=ok, port tanpa
         process terikat) - BUKAN nama aplikasi.
      4. Untuk tiap kandidat: DiagnosisEngine.investigate(entity, graph)
         -> List[Hypothesis] (berbasis evidence, fail-closed INSUFFICIENT).
      5. Map tiap Hypothesis yang punya evidence -> satu entry findings
         {finding_id, subject_id, label, evidence, confidence}.
         - confidence = numeric dari ConfidenceAssessor.confidence_score.
         - bila SEMUA hypotheses tidak confident / tak ada evidence ->
           InvestigationResult dengan findings kosong + summary INSUFFICIENT jujur
           (TIDAK mengarang, TIDAK menyimpulkan root cause).
      6. Wrap jadi InvestigationResult (successful=True bila investigasi
         berjalan; bukan berarti menemukan penyebab).

    `result.limit` membatasi jumlah kandidat yang diinvestigasi (amankan
    timeout UI); default 8 (paralel dengan adaptive pipeline).

    Adapter HANYA menerjemahkan; TIDAK menjadi tempat menambahkan fakta baru.
    """

    def __init__(self, subject: SubjectRef,
                 discovery=None,
                 diagnosis_engine=None,
                 candidate_limit: int = 8) -> None:
        self._subject = subject
        if discovery is None:
            from sam.environment.discovery import EnvironmentDiscovery
            discovery = EnvironmentDiscovery()
        self._discovery = discovery
        if diagnosis_engine is None:
            from sam.environment.diagnosis import DiagnosisEngine
            diagnosis_engine = DiagnosisEngine()
        self._engine = diagnosis_engine
        self._candidate_limit = candidate_limit

    def investigate(self, *, evidence: Dict[str, Any] = None,
                    capability: str = "investigate") -> InvestigationResult:
        """Investigate environment dari facts observasi real.

        `evidence` (opsional) adalah hasil observation R1-002; tidak wajib
        dipakai DiagnosisEngine (yang butuh Entity+EntityGraph), tapi
        direkam sebagai evidence_ref konteks untuk traceability.
        """
        # 1. discovery real
        try:
            scan = self._discovery.discover()
        except Exception as exc:  # pragma: no cover - defensif
            return InvestigationResult(
                subject=self._subject,
                successful=False,
                findings=[],
                evidence_ref="environment investigation gagal total",
                summary="environment investigation gagal: " + str(exc),
                error=str(exc),
            )

        entities = list(getattr(scan, "entities", None) or [])
        if not entities:
            # Tidak ada entitas -> tidak ada evidence -> INSUFFICIENT jujur
            # (bukan "tidak ada masalah"; discovery kosong/gagal).
            return InvestigationResult(
                subject=self._subject,
                successful=True,
                findings=[],
                evidence_ref="environment discovery kosong",
                summary="environment tampak tidak menghasilkan fakta yang dapat "
                        "diinvestigasi (probe kosong/gagal) - tidak mengarang temuan.",
                error="",
            )

        # 2. graph
        from sam.environment.graph import EntityGraph
        graph = EntityGraph.from_scan(entities)

        # 3. kandidat dari fakta health (pola adaptive pipeline, bukan nama app)
        candidates = self._select_candidates(entities)
        candidates.sort(key=lambda c: c[1], reverse=True)
        candidates = candidates[:self._candidate_limit]

        # 4+5. investigasi per kandidat -> hypotheses -> findings
        findings: List[Dict[str, Any]] = []
        investigated: List[str] = []
        for ent, _priority, reason in candidates:
            hypotheses = self._engine.investigate(ent, graph)
            investigated.append(ent.id)
            for h in hypotheses:
                if not h.evidence:
                    continue  # hypothesis tanpa evidence -> tidak direkam
                # confidence numeric dari evidence (jujur, via assessor yang
                # memakai engine yang sama). INSUFFICIENT -> tetap dicatat
                # sebagai indecisive, BUKAN root cause.
                conf = self._numeric_confidence(h.evidence)
                findings.append({
                    "finding_id": _stable_id(ent.id, h.statement),
                    "subject_id": self._subject.subject_id,
                    "label": h.statement,
                    "entity": {
                        "id": ent.id,
                        "kind": ent.kind.value if hasattr(ent.kind, "value") else str(getattr(ent, "kind", "")),
                        "source": ent.source.value if hasattr(ent.source, "value") else str(getattr(ent, "source", "")),
                        "label": str(getattr(ent, "label", "")),
                    },
                    "evidence": [e.as_dict() for e in h.evidence],
                    "confidence": conf,
                    # JELAS: ini dugaan kandidat berdasar evidence, BUKAN
                    # penyebab final (root cause = R1-004).
                    "claim": "candidate",
                })

        # 6. ringkasan jujur
        if findings:
            summary = ("Ditemukan {} temuan kandidat dari {} entitas "
                       "environment nyata (read-only). Temuan ini adalah "
                       "kandidat berdasar evidence, bukan penyebab final.")
            summary = summary.format(len(findings), len(entities))
        else:
            summary = ("evidence observasi tidak cukup untuk menghasilkan "
                       "temuan kandidat yang yakin - INSUFFICIENT, tidak mengarang. "
                       "Perlu observasi lebih (CPU/mem/disk) yang belum dilakukan.")

        return InvestigationResult(
            subject=self._subject,
            successful=True,
            findings=findings,
            evidence_ref=_evidence_ref(evidence),
            summary=summary,
            error="",
        )

    # --- kandidat generik dari fakta health (BUKAN nama aplikasi) ---
    @staticmethod
    def _select_candidates(entities) -> List[Any]:
        """Pilih kandidat dari fakta observasi yang MENARIK PERHATIAN:
        proses dengan health != ok, dan port tanpa process terikat.

        Proses sehat (health=ok) TIDAK dijadikan finding kandidat - itu hanya
        observasi kehadiran, bukan sinyal masalah, dan akan membuat INSUFFICIENT
        hampir mustahil dicapai. R1-003: berhenti di finding kandidat yang
        menandakan sesuatu memang layak diselidiki, atau INSUFFICIENT bila tidak
        ada sinyal -> jujur (tidak mengarang masalah).

        Ini pola yang sama dengan AdaptiveEnvironmentPipeline (nanti direuse
        utuh bila pipeline diangkat ke jalur user); di sini minimal & generik."""
        out: List[Any] = []
        from sam.environment.entity import EntityKind
        for e in entities:
            kind = e.kind
            if kind == EntityKind.PROCESS:
                health = e.attributes.get("health")
                if health and health != "ok":
                    out.append((e, 70, f"process status={health}"))
            elif kind == EntityKind.PORT:
                pid = e.attributes.get("pid")
                if not pid:
                    out.append((e, 60, "port without bound process"))
            # FILE: tidak punya valid_signature di discovery -> jangan paksa
            # kandidat (kalau ada fakta baru di masa depan muncul otomatis).
        return out

    @staticmethod
    def _numeric_confidence(evidence: List) -> float:
        """Terjemahkan evidence menjadi confidence 0..1 (jujur, via assessor
        yang sama dipakai DiagnosisEngine, tanpa panggil ulang engine)."""
        try:
            from sam.environment.confidence import ConfidenceAssessor
            return round(float(ConfidenceAssessor().confidence_score(evidence)), 2)
        except Exception:  # pragma: no cover - defensif
            return 0.0


def _stable_id(entity_id: str, statement: str) -> str:
    import hashlib
    raw = "{}|{}".format(entity_id, statement).encode("utf-8")
    return "fnd-" + hashlib.sha256(raw).hexdigest()[:12]


def _evidence_ref(evidence: Optional[Dict[str, Any]]) -> str:
    """Referensi ke observation yang membentuk konteks (traceability).

    Kalau `evidence` observation R1-002 diberikan, tautkan ke timestamp/source.
    Tidak pernah menyimpan secret/raw lengkap di sini.
    """
    if not evidence:
        return "environment discovery (fresh scan)"
    ts = evidence.get("timestamp")
    sources = evidence.get("sources")
    if sources:
        return "observation sources={}; ts={}".format(
            ",".join(str(s) for s in sources), ts or "-")
    return "observation ts={}".format(ts or "-")
