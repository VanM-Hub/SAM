"""Environment-adaptive: mesin diagnosis tanpa asumsi jenis aplikasi.

SAM TIDAK tahu (dan TIDAK peduli) apakah entitas itu Word/OpenClaw/Chrome.
Yang SAM tahu: entitas dengan fakta observasi, relasi graph, dan evidence.

Diagnosis:
  1. Terima satu entitas (candidate ward) + graph + kumpulan evidence.
  2. Pilih strategi investigation berdasarkan evidence yang tersedia
     (bukan jenis aplikasi).
  3. Adaptif: bila satu sumber observasi gagal, coba sumber lain.
  4. Akhiri dengan ConfidenceLevel + root cause; bila evidence tidak cukup,
     SAM menyatakan "evidence tidak cukup" (INSUFFICIENT) - TIDAK mengarang.

Hasil diagnosis JUJUR: sebab-sebab (hypotheses) diberi confidence, dan
SAM hanya merekomendasikan remediasi bila confidence memenuhi ambang.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from sam.environment.confidence import (
    ConfidenceAssessor,
    ConfidenceLevel,
    Evidence,
)
from sam.environment.entity import Entity, EntityKind
from sam.environment.graph import EntityGraph


@dataclass
class Hypothesis:
    """Satu dugaan root cause (berbasis evidence, bukan asumsi)."""

    statement: str
    evidence: List[Evidence] = field(default_factory=list)
    level: Optional[ConfidenceLevel] = None
    confident: bool = False  # level >= MEDIUM

    def assess(self, assessor: ConfidenceAssessor) -> "Hypothesis":
        self.level = assessor.assess(self.evidence)
        self.confident = self.level in (
            ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)
        return self

    def as_dict(self) -> Dict[str, Any]:
        return {
            "statement": self.statement,
            "level": self.level.value if self.level else None,
            "confident": self.confident,
            "evidence": [e.as_dict() for e in self.evidence],
        }


# Tanda/observable generik yang bisa memicu dugaan (bukan nama aplikasi).
# Ini adalah POLA KELAS MASALAH pada environment nyata, bukan katalog app.
@dataclass
class Observable:
    name: str
    probe: Callable[[Entity, EntityGraph], List[Evidence]]


class DiagnosisEngine:
    """Mesin diagnosis generik.

    Strategy: buat beberapa hipotesis dari EVIDENCE yang benar-benar
    terobservasi (disk nyaris penuh, proses tak sehat, port ditutup, file
    tak valid). Bila tidak ada evidence -> INSUFFICIENT.
    """

    def __init__(self, assessor: Optional[ConfidenceAssessor] = None) -> None:
        self._assessor = assessor or ConfidenceAssessor()
        # Pustaka OBSERVABLE generik (bukan katalog aplikasi).
        self._observables: List[Observable] = [
            Observable("disk_space", self._obs_disk_space),
            Observable("process_health", self._obs_process_health),
            Observable("port_availability", self._obs_port_availability),
            Observable("file_integrity", self._obs_file_integrity),
        ]

    # --- pemeriksaan generik (semua berbasis fakta) ---

    def _obs_disk_space(self, target: Entity, g: EntityGraph) -> List[Evidence]:
        free = target.attributes.get("disk_free_bytes")
        total = target.attributes.get("disk_total_bytes")
        if free is None or total is None:
            return []
        pct = (free / total) * 100 if total else 0
        if pct < 10:
            return [Evidence("disk_space", f"free {pct:.1f}% < 10% warning",
                             strength=0.9)]
        if pct < 20:
            return [Evidence("disk_space", f"free {pct:.1f}% < 20% cautious",
                             strength=0.5)]
        return [Evidence("disk_space", f"free {pct:.1f}% ok", strength=0.9,
                         negative=False)]

    def _obs_process_health(self, target: Entity, g: EntityGraph) -> List[Evidence]:
        health = target.attributes.get("health")
        if health is None:
            return []
        if health == "ok":
            return [Evidence("process_table", f"process {target.label} healthy",
                             strength=0.8)]
        return [Evidence("process_table",
                         f"process {target.label} status={health}",
                         strength=0.8)]

    def _obs_port_availability(self, target: Entity, g: EntityGraph) -> List[Evidence]:
        if target.kind != EntityKind.PORT:
            return []
        # port dengan pid kosong = listening tanpa process teridentifikasi
        pid = target.attributes.get("pid")
        if not pid:
            return [Evidence("port_table",
                             f"port {target.label} no process bound",
                             strength=0.6)]
        return [Evidence("port_table", f"port {target.label} bound pid={pid}",
                         strength=0.8)]

    def _obs_file_integrity(self, target: Entity, g: EntityGraph) -> List[Evidence]:
        if target.kind != EntityKind.FILE:
            return []
        sig = target.attributes.get("valid_signature")
        if sig is None:
            return []
        if sig:
            return [Evidence("file_integrity",
                             f"file {target.label} signature valid",
                             strength=0.8)]
        return [Evidence("file_integrity",
                         f"file {target.label} signature INVALID",
                         strength=0.9)]

    # --- API ---

    def investigate(self, target: Entity, g: EntityGraph,
                    observables: Optional[List[str]] = None) -> List[Hypothesis]:
        """Buat hipotesis dari evidence yang benar-benar ada (tanpa asumsi)."""
        hypothesis = Hypothesis(
            statement=f"investigate {target.label} "
                      f"({target.kind.value}/{target.source.value})")
        selected = self._observables
        if observables:
            selected = [o for o in self._observables if o.name in observables]
        # adaptif: kumpulkan evidence dari semua observables; bila satu gagal
        # (exception), kita tetap lanjut ke yang lain (sumber lain).
        for obs in selected:
            try:
                hypothesis.evidence.extend(obs.probe(target, g))
            except Exception:
                continue  # satu sumber gagal -> coba sumber lain (adaptif)
        hypothesis.assess(self._assessor)
        return [hypothesis] if hypothesis.evidence else [
            Hypothesis(statement="evidence tidak cukup - tidak mengarang",
                       level=ConfidenceLevel.INSUFFICIENT)
        ]

    def assess(self, evidence: List[Evidence]) -> ConfidenceLevel:
        return self._assessor.assess(evidence)
