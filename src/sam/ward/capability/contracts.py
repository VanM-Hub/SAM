# Ward Generalized Capability Contracts - M13-004..007
#
# Kunci M13: kemampuan internal yang sudah ada JANGAN diduplikasi. Sebuah
# capability punya satu SEMANTIC MODEL, dan menerima SUBJECT yang dapat
# berupa Citizen ataupun Ward.
#
#   observe(subject)   -> ObservationPort -> Adapter -> real subject -> Evidence
#   investigate(subject) -> InvestigationTarget -> engine investigation existing
#   diagnose(evidence) -> Finding -> Confidence
#   recover(finding)   -> Recommendation -> Approval -> Canonical Execution -> Verification
#
# Di sini kita definisikan KONTRAK (protocol/abstract) yang reusable; bukan
# engine baru. Implementasi Ward merealisasikan kontrak ini dengan memakai
# RealExecutionHarness (single execution authority) + canonical connector
# (infrastructure adapter). Tidak ada executor kedua.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


# ---------------------------------------------------------------------------
# Subject: abstraksi "Citizen | Ward" agar capability punya satu semantic model
# ---------------------------------------------------------------------------
class Subject(Protocol):
    """Sebuah subjek yang dapat dioperasikan: Citizen (internal) ATAU Ward (external)."""

    @property
    def subject_id(self) -> str: ...
    @property
    def subject_type(self) -> str: ...
    def as_dict(self) -> Dict[str, Any]: ...


@dataclass(frozen=True)
class SubjectRef:
    """Referensi subjek seragam (Citizen ATAU Ward)."""

    subject_id: str
    subject_type: str          # "citizen" | "ward"
    kind: str = ""             # citizen kind / ward_type
    name: str = ""

    @property
    def is_ward(self) -> bool:
        return self.subject_type == "ward"

    @property
    def is_citizen(self) -> bool:
        return self.subject_type == "citizen"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "kind": self.kind,
            "name": self.name,
        }


# ---------------------------------------------------------------------------
# M13-004 Observation
# ---------------------------------------------------------------------------
class ObservationTarget(Protocol):
    """Kontrak target observasi. Direalisasikan oleh CitizenObservationTarget
    ATAU WardObservationTarget. Engine/port observation sebelah HANYA tahu
    kontrak ini (bukan jenis subject)."""

    def observe(self, *, capability: str = "observe") -> "Observation": ...


@dataclass(frozen=True)
class Observation:
    """Hasil observasi satu subject: data real + evidence terverifikasi."""

    subject: SubjectRef
    capability: str
    successful: bool
    payload: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.successful

    def as_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject.as_dict(),
            "capability": self.capability,
            "successful": self.successful,
            "payload": self.payload,
            "evidence": self.evidence,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# M13-005 Investigation
# ---------------------------------------------------------------------------
class InvestigationTarget(Protocol):
    """Kontrak target investigasi. Realisasi Citizen/Ward memakai engine
    investigation existing (bukan ExternalInvestigationEngine baru)."""

    def investigate(self, *, evidence: Dict[str, Any],
                    capability: str = "investigate") -> "InvestigationResult": ...


@dataclass(frozen=True)
class InvestigationResult:
    """Hasil investigasi satu subject."""

    subject: SubjectRef
    successful: bool
    findings: List[Dict[str, Any]] = field(default_factory=list)
    evidence_ref: str = ""
    summary: str = ""
    error: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject.as_dict(),
            "successful": self.successful,
            "findings": self.findings,
            "evidence_ref": self.evidence_ref,
            "summary": self.summary,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# M13-006 Diagnosis
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Finding:
    """Temuan dari diagnosis berbasis evidence subject."""

    finding_id: str
    subject_id: str
    label: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "subject_id": self.subject_id,
            "label": self.label,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


# ---------------------------------------------------------------------------
# M13-007 Recovery (canonical - tidak ada jalur langsung ke connector)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Recommendation:
    """Rekomendasi aksi (mutation). HANYA berlaku via approval + canonical."""

    recommendation_id: str
    subject_id: str
    action: str                # capability mutation (e.g. "protect", "mutate")
    target: str = ""
    rationale: str = ""
    approval_required: bool = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "subject_id": self.subject_id,
            "action": self.action,
            "target": self.target,
            "rationale": self.rationale,
            "approval_required": self.approval_required,
        }
