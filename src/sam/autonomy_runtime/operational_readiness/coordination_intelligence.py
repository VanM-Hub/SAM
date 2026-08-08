# Autonomous Coordination Intelligence - WP-43
# IP-3.2-005 (AO-3.2-001 / ED-3.2-005)
#
# Mengevaluasi koordinasi antara berbagai penilaian/proposal agar menjadi satu
# pandangan yang konsisten. Mengkorelasikan diagnosa, mengonsolidasikan proposal
# dari sudut coordination & lifecycle, dan mendeteksi inkonsistensi antar-runtime.
# Prinsip: "Aggregation != Decision; Recommendation != Authority."
# HANYA mengevaluasi & menyusun konsistensi - TIDAK memilih/menjalankan.
# Deterministic.

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.operational_readiness.models import (
    OperationalReadiness,
    ReadinessInput,
)


@dataclass(frozen=True)
class ConsistencyFinding:
    """Satu temuan konsistensi antar penilaian (immutable)."""

    finding_id: str
    kind: str  # consistent | conflict | gap
    subject: str
    detail: str
    involves: Tuple[str, ...] = ()  # artifact_id yang terlibat

    def as_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "kind": self.kind,
            "subject": self.subject,
            "detail": self.detail,
            "involves": list(self.involves),
        }


@dataclass(frozen=True)
class CoordinationIntelligence:
    """Intelijen koordinasi antar penilaian (immutable, proposal-only)."""

    intelligence_id: str
    readiness_id: str
    consistency: Tuple[ConsistencyFinding, ...] = ()
    aligned: bool = True
    coordination_notes: Tuple[str, ...] = ()
    is_proposal_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "intelligence_id": self.intelligence_id,
            "readiness_id": self.readiness_id,
            "consistency": [c.as_dict() for c in self.consistency],
            "aligned": self.aligned,
            "coordination_notes": list(self.coordination_notes),
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }

    def finding_count(self) -> int:
        return len(self.consistency)

    def conflict_count(self) -> int:
        return sum(1 for c in self.consistency if c.kind == "conflict")


class AutonomousCoordinationIntelligence:
    """Mengkorelasikan diagnosa & mengkonsolidasikan proposal (deterministik)."""

    def analyze(
        self,
        readiness: OperationalReadiness,
        intelligence_id: str = "",
    ) -> CoordinationIntelligence:
        findings: List[ConsistencyFinding] = []
        notes: List[str] = []

        by_source: Dict[str, List[ReadinessInput]] = {}
        for i in readiness.inputs:
            by_source.setdefault(i.source, []).append(i)

        # 1) Konsistensi kesehatan (observation vs diagnostics)
        obs = by_source.get("observation", [])
        diag = by_source.get("diagnostics", [])
        healthy_snapshots = self._health_agg(obs) if obs else None
        diag_agg = self._health_agg(diag) if diag else None
        if healthy_snapshots is not None and diag_agg is not None:
            if _same_bucket(healthy_snapshots, diag_agg):
                findings.append(ConsistencyFinding(
                    finding_id=self._stable_id("cons-obs-diag"),
                    kind="consistent", subject="observe-diagnose",
                    detail="observation & diagnostics agree on health",
                    involves=tuple(i.artifact_id for i in (obs + diag)),
                ))
            else:
                findings.append(ConsistencyFinding(
                    finding_id=self._stable_id("conf-obs-diag"),
                    kind="conflict", subject="observe-diagnose",
                    detail="observation & diagnostics disagree on health",
                    involves=tuple(i.artifact_id for i in (obs + diag)),
                ))
                notes.append("observe/diagnose conflict flagged")

        # 2) Koordinasi: readiness recovery & coordination selaras
        rec = by_source.get("recovery", [])
        coord = by_source.get("coordination", [])
        if rec and coord:
            rec_ok = all(self._status_ready(i.status) for i in rec)
            coord_ok = all(self._status_ready(i.status) for i in coord)
            if rec_ok == coord_ok:
                findings.append(ConsistencyFinding(
                    finding_id=self._stable_id("cons-rec-coord"),
                    kind="consistent", subject="recover-coordinate",
                    detail="recovery & coordination readiness aligned",
                    involves=tuple(i.artifact_id for i in (rec + coord)),
                ))
                notes.append("recovery/coordination aligned")
            else:
                findings.append(ConsistencyFinding(
                    finding_id=self._stable_id("conf-rec-coord"),
                    kind="conflict", subject="recover-coordinate",
                    detail="recovery & coordination readiness misaligned",
                    involves=tuple(i.artifact_id for i in (rec + coord)),
                ))
                notes.append("recovery/coordination conflict flagged")

        # 3) Lifecycle vs readiness
        lc = by_source.get("lifecycle", [])
        rd = by_source.get("readiness", [])
        if lc and rd:
            lc_ok = all(self._status_ready(i.status) for i in lc)
            rd_ok = all(self._status_ready(i.status) for i in rd)
            if lc_ok == rd_ok:
                findings.append(ConsistencyFinding(
                    finding_id=self._stable_id("cons-lc-rd"),
                    kind="consistent", subject="lifecycle-readiness",
                    detail="lifecycle understanding & readiness aligned",
                    involves=tuple(i.artifact_id for i in (lc + rd)),
                ))
            else:
                findings.append(ConsistencyFinding(
                    finding_id=self._stable_id("gap-lc-rd"),
                    kind="gap", subject="lifecycle-readiness",
                    detail="lifecycle & readiness mismatch suggests transition context",
                    involves=tuple(i.artifact_id for i in (lc + rd)),
                ))
                notes.append("lifecycle/readiness gap noted")

        # 4) Gap: sumber yang hilang
        if readiness.metadata.get("missing_sources"):
            for src in readiness.metadata["missing_sources"]:
                findings.append(ConsistencyFinding(
                    finding_id=self._stable_id("gap-{}".format(src)),
                    kind="gap", subject="source-{}".format(src),
                    detail="no input for {} source".format(src),
                    involves=tuple(readiness.readiness_id),
                ))
                notes.append("{} source missing".format(src))

        aligned = not any(c.kind == "conflict" for c in findings)
        return CoordinationIntelligence(
            intelligence_id=intelligence_id or self._stable_id(readiness.readiness_id),
            readiness_id=readiness.readiness_id,
            consistency=tuple(findings),
            aligned=aligned,
            coordination_notes=tuple(dict.fromkeys(notes)),
            is_proposal_only=True,
            metadata={"deterministic": True},
        )

    @staticmethod
    def _health_agg(items: Tuple[ReadinessInput, ...]) -> str:
        if not items:
            return "unknown"
        bucket = {"healthy": 1, "degraded": 0, "unhealthy": -1, "unknown": 0}
        total = sum(bucket.get(i.health, 0) for i in items)
        if total > 0:
            return "healthy"
        if total < 0:
            return "unhealthy"
        return "degraded"

    @staticmethod
    def _status_ready(status: str) -> bool:
        return status in ("ready", "healthy")

    @staticmethod
    def _stable_id(seed: str) -> str:
        return "ci-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]


def _same_bucket(a: str, b: str) -> bool:
    return a == b
