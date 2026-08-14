# Ward Governor - Universal Governance Engine for a Ward subject
#
# Satu semantic governance engine yang menjalankan:
#   observe(subject) -> investigate(subject) -> recommend(subject)
#   -> [approve] -> canonical execute -> verify -> learn/audit
#
# Model akhir M13:
#   SAM -> (Citizen | Ward) -> Universal Governance Engine
#                          -> Observation -> Investigation -> Learning
#                          -> Recommendation -> Approval -> Canonical Execution
#                          -> Verification -> Audit
#
# BOUNDARY (M13-010) SELALU diperiksa sebelum aksi; connector TIDAK pernah
# menilai izin sendiri. Mutation SELALU lewat approval canonical + canonical
# execution (RealExecutionHarness). TIDAK ada jalur langsung ke connector.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from sam.ward.capability.contracts import (
    Observation, InvestigationResult, Finding, Recommendation, SubjectRef,
    ObservationTarget, InvestigationTarget,
)
from sam.ward.governance.boundary import WardGovernanceBoundary, AuthorizationResult
from sam.ward.registry.registry import WardRepository


@dataclass
class WardMissionOutcome:
    """Hasil satu siklus goveranance terhadap Ward (deterministik, auditable)."""

    subject: SubjectRef
    capability: str
    authorized: bool
    steps: List[Dict[str, Any]] = field(default_factory=list)
    observation: Optional[Observation] = None
    investigation: Optional[InvestigationResult] = None
    finding: Optional[Finding] = None
    recommendation: Optional[Recommendation] = None
    execution_result: Optional[Dict[str, Any]] = None
    audit: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, step: str, detail: Dict[str, Any]) -> None:
        self.steps.append({"step": step, "detail": detail})

    def as_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject.as_dict(),
            "capability": self.capability,
            "authorized": self.authorized,
            "steps": self.steps,
            "observation": self.observation.as_dict() if self.observation else None,
            "investigation": self.investigation.as_dict() if self.investigation else None,
            "finding": self.finding.as_dict() if self.finding else None,
            "recommendation": self.recommendation.as_dict() if self.recommendation else None,
            "execution_result": self.execution_result,
            "audit": self.audit,
        }


class WardGovernor:
    """Governance engine untuk subject Ward (atau Citizen via kontrak reusable).

    Menjalankan alur canonical. Keputusan izin ada di WardGovernanceBoundary.
    Mutation dieksekusi lewat canonical executor yang DISUNTIKKAN dari luar
    (application/runtime composition root) - governor TIDAK menyimpan authority.
    """

    def __init__(self, repository: WardRepository,
                 boundary: Optional[WardGovernanceBoundary] = None,
                 canonical_executor: Optional[Callable[[Recommendation, SubjectRef],
                                                       Dict[str, Any]]] = None) -> None:
        self._repo = repository
        self._boundary = boundary or WardGovernanceBoundary(repository)
        # canonical_executor = fungsi yang menjalankan mutation via
        # RealExecutionHarness + ApprovalGate. Dikosongkan kalau belum di-wire.
        self._canonical_executor = canonical_executor

    # --- observation (read) ---

    def observe(self, subject: SubjectRef, target: ObservationTarget,
                *, capability: str = "observe") -> WardMissionOutcome:
        outcome = WardMissionOutcome(subject=subject, capability=capability,
                                     authorized=False)
        auth = self._boundary.can_observe(subject.subject_id, capability)
        outcome.record("authorize", auth.as_dict())
        if not auth.allowed:
            outcome.authorized = False
            outcome.audit.append({"step": "observe", "verdict": "BLOCKED",
                                  "reason": auth.reason, "subject": subject.as_dict()})
            return outcome
        outcome.authorized = True
        obs = target.observe(capability=capability)
        outcome.observation = obs
        outcome.record("observe", obs.as_dict())
        outcome.audit.append({"step": "observe",
                              "verdict": "OK" if obs.ok else "FAILED",
                              "subject": subject.as_dict(),
                              "evidence": obs.evidence})
        return outcome

    # --- investigate (read) ---

    def investigate(self, subject: SubjectRef,
                    target: InvestigationTarget,
                    *, capability: str = "investigate",
                    evidence: Optional[Dict[str, Any]] = None) -> WardMissionOutcome:
        """Investigate subject. `evidence` opsional: hasil observation dari
        langkah `observe` (harus reuse evidence yang sudah dikumpulkan, bukan
        menebak). Bila kosong, evidence dianggap belum ada (fail honest)."""
        outcome = WardMissionOutcome(subject=subject, capability=capability,
                                     authorized=False)
        auth = self._boundary.can_observe(subject.subject_id, capability)
        outcome.record("authorize", auth.as_dict())
        if not auth.allowed:
            outcome.audit.append({"step": "investigate", "verdict": "BLOCKED",
                                  "reason": auth.reason})
            return outcome
        outcome.authorized = True
        res = target.investigate(evidence=evidence or {}, capability=capability)
        outcome.investigation = res
        outcome.record("investigate", res.as_dict())
        outcome.audit.append({"step": "investigate", "verdict": "OK",
                              "findings": res.findings})
        return outcome

    # --- recommend (read - mutation only via approval) ---

    def recommend(self, subject: SubjectRef, *,
                  action: str = "protect", target: str = "",
                  rationale: str = "") -> WardMissionOutcome:
        outcome = WardMissionOutcome(subject=subject, capability=action,
                                     authorized=False)
        auth = self._boundary.can_mutate(subject.subject_id, action)
        outcome.record("authorize-mutation", auth.as_dict())
        if not auth.allowed:
            outcome.audit.append({"step": "recommend", "verdict": "BLOCKED",
                                  "reason": auth.reason})
            return outcome
        outcome.authorized = True
        outcome.recommendation = Recommendation(
            recommendation_id=subject.subject_id + ":protect",
            subject_id=subject.subject_id, action=action,
            target=target, rationale=rationale,
            approval_required=auth.requires_approval)
        outcome.record("recommend", outcome.recommendation.as_dict())
        outcome.audit.append({"step": "recommend", "verdict": "PENDING-APPROVAL",
                              "approval_required": True})
        return outcome

    # --- execute mutation (REQUIRES approve flag + canonical executor) ---

    def execute(self, subject: SubjectRef, *, recommendation: Optional[Recommendation] = None,
                approved: bool, approver: str = "") -> WardMissionOutcome:
        """Jalankan recommendation yang sudah disetujui via canonical executor.

        `approved` harus True (approval canonical sudah didapat) ATAU deny.
        `recommendation` = rekomendasi dari level atas (opsional; bila kosong,
        outcome.recommendation dari langkah `recommend` dipakai).
        TIDAK ada jalur mutation tanpa approval.
        """
        outcome = WardMissionOutcome(subject=subject, capability="execute",
                                     authorized=False)
        # rekam recommendation bila diberikan
        if recommendation is not None:
            outcome.recommendation = recommendation
        if not self._canonical_executor:
            outcome.audit.append({"step": "execute", "verdict": "BLOCKED",
                                  "reason": "no canonical executor wired"})
            return outcome
        if not approved:
            outcome.authorized = False
            outcome.audit.append({"step": "execute", "verdict": "DENIED",
                                  "reason": "approval required but not granted"})
            return outcome
        # mutation authorization di-periksa ulang (defense in depth)
        auth = self._boundary.can_mutate(subject.subject_id, "protect")
        if not auth.allowed:
            outcome.audit.append({"step": "execute", "verdict": "BLOCKED",
                                  "reason": auth.reason})
            return outcome
        outcome.authorized = True
        outcome.record("execute", {"approved": True, "approver": approver})
        if outcome.recommendation is None:
            outcome.audit.append({"step": "execute", "verdict": "BLOCKED",
                                  "reason": "no recommendation to execute"})
            return outcome
        result = self._canonical_executor(outcome.recommendation, subject)
        outcome.execution_result = result
        outcome.audit.append({"step": "execute", "verdict": "OK",
                              "approver": approver,
                              "result": result,
                              "subject": subject.as_dict()})
        return outcome
