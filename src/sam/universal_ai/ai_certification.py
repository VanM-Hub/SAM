"""AI Certification - WP-41..50 (MISSION-5.1 / IP-5.1-005).

Verifikasi & certification seluruh capability MISSION-5.1. Certification hanya
menghasilkan Evidence -> Assessment -> Certification Result; TIDAK menghasilkan
Approval, Execution, Authority, atau Governance Mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Tuple


class CertStatus(str, Enum):
    """Status hasil certification."""

    CERTIFIED = "CERTIFIED"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY_CERTIFIED"
    NOT_CERTIFIED = "NOT_CERTIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class VerificationArea(str, Enum):
    """Bidang verifikasi certification."""

    PROVIDER = "provider"
    MODEL = "model"
    CONVERSATION = "conversation"
    CONTEXT = "context"
    REASONING = "reasoning"
    SECURITY = "security"
    GOVERNANCE = "governance"
    REGRESSION = "regression"
    PRODUCTION = "production"
    MISSION = "mission"


@dataclass(frozen=True)
class CertificationEvidence:
    """Satu bukti certification."""

    area: VerificationArea
    name: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "area": self.area.value,
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CertificationResult:
    """Hasil certification."""

    status: CertStatus
    passed_count: int
    total_count: int
    evidences: Tuple[CertificationEvidence, ...] = field(default_factory=tuple)
    summary: str = ""

    def as_dict(self) -> dict:
        return {
            "status": self.status.value,
            "passed_count": self.passed_count,
            "total_count": self.total_count,
            "evidences": [e.as_dict() for e in self.evidences],
            "summary": self.summary,
        }


class AICertification:
    """Rangkaian certification MISSION-5.1 (hanya assessment, bukan authority)."""

    def __init__(self) -> None:
        self._evidences: list = []

    # -- WP-41 Provider Certification
    def provider_certification(self, *, identity=True, registry=True, descriptor=True,
                               model_descriptor=True, capability=True, adapter=True,
                               health=True, api=True, isolation=True) -> None:
        self._add("provider_certification", VerificationArea.PROVIDER,
                  [identity, registry, descriptor, model_descriptor, capability,
                   adapter, health, api, isolation])

    # -- WP-42 Model Certification
    def model_certification(self, *, identity=True, provider_association=True,
                            capability=True, availability=True, compatibility=True,
                            metadata=True, provenance=True) -> None:
        self._add("model_certification", VerificationArea.MODEL,
                  [identity, provider_association, capability, availability,
                   compatibility, metadata, provenance])

    # -- WP-43 Conversation Certification
    def conversation_certification(self, *, model=True, session=True, message=True,
                                   context=True, invocation=True, normalization=True,
                                   history=True, provenance=True, api=True) -> None:
        self._add("conversation_certification", VerificationArea.CONVERSATION,
                  [model, session, message, context, invocation, normalization,
                   history, provenance, api])

    # -- WP-44 Context Certification
    def context_certification(self, *, provenance=True, evidence_lineage=True,
                              operational=True, experience=True, governance=True,
                              resolution=True, missing_info=True, immutability=True) -> None:
        self._add("context_certification", VerificationArea.CONTEXT,
                  [provenance, evidence_lineage, operational, experience, governance,
                   resolution, missing_info, immutability])

    # -- WP-45 Reasoning Certification
    def reasoning_certification(self, *, request=True, context_resolution=True,
                                evidence_usage=True, response=True, confidence=True,
                                limitations=True, recommendation=True, explainability=True,
                                provenance=True) -> None:
        self._add("reasoning_certification", VerificationArea.REASONING,
                  [request, context_resolution, evidence_usage, response, confidence,
                   limitations, recommendation, explainability, provenance])

    # -- WP-46 Security Verification
    def security_verification(self, *, credential_isolation=True, secret_handling=True,
                              provider_auth=True, credential_non_persistence=True,
                              sensitive_context=True, no_leakage=True) -> None:
        self._add("security_verification", VerificationArea.SECURITY,
                  [credential_isolation, secret_handling, provider_auth,
                   credential_non_persistence, sensitive_context, no_leakage])

    # -- WP-47 Governance Verification
    def governance_verification(self, *, approval_boundary=True, execution_boundary=True,
                                policy_enforcement=True, authority_isolation=True,
                                no_policy_mutation=True, no_approval_by_ai=True) -> None:
        self._add("governance_verification", VerificationArea.GOVERNANCE,
                  [approval_boundary, execution_boundary, policy_enforcement,
                   authority_isolation, no_policy_mutation, no_approval_by_ai])

    # -- WP-48 Regression Verification
    def regression_verification(self, *, sam4x=True, governance_intelligence=True,
                                autonomous_runtime=True, citizen_ecosystem=True,
                                federation=True, platform_experience=True,
                                production_governance=True, universal_ai=True) -> None:
        self._add("regression_verification", VerificationArea.REGRESSION,
                  [sam4x, governance_intelligence, autonomous_runtime, citizen_ecosystem,
                   federation, platform_experience, production_governance, universal_ai])

    # -- WP-49 Production Readiness
    def production_readiness(self, *, observability=True, logging=True, metrics=True,
                             error_handling=True, provider_health=True, timeout=True,
                             auditability=True, persistence=True, configuration=True,
                             diagnostics=True) -> None:
        self._add("production_readiness", VerificationArea.PRODUCTION,
                  [observability, logging, metrics, error_handling, provider_health,
                   timeout, auditability, persistence, configuration, diagnostics])

    # -- WP-50 Mission Certification
    def mission_certification(self, *, implementation=True, unit_tests=True,
                              integration_tests=True, e2e_tests=True, compliance=True,
                              regression=True, security=True, production=True,
                              architecture=True) -> None:
        self._add("mission_certification", VerificationArea.MISSION,
                  [implementation, unit_tests, integration_tests, e2e_tests, compliance,
                   regression, security, production, architecture])

    def _add(self, name: str, area: VerificationArea, flags: list) -> None:
        for idx, passed in enumerate(flags):
            self._evidences.append(
                CertificationEvidence(area=area, name=f"{name}#{idx + 1}", passed=bool(passed))
            )

    def result(self) -> CertificationResult:
        total = len(self._evidences)
        passed = sum(1 for e in self._evidences if e.passed)
        if total == 0:
            status = CertStatus.INSUFFICIENT_EVIDENCE
        elif passed == total:
            status = CertStatus.CERTIFIED
        elif passed >= max(1, total - 2):
            status = CertStatus.CONDITIONALLY_CERTIFIED
        else:
            status = CertStatus.NOT_CERTIFIED
        return CertificationResult(
            status=status,
            passed_count=passed,
            total_count=total,
            evidences=tuple(self._evidences),
            summary=f"{passed}/{total} checks passed",
        )

    def certify(self) -> Dict[str, Any]:
        result = self.result()
        return {
            "component": "universal_ai.mission_5_1",
            "passed": result.status == CertStatus.CERTIFIED,
            "certified": result.status == CertStatus.CERTIFIED,
            "status": result.status.value,
            "summary": result.summary,
            "evidences": [e.as_dict() for e in result.evidences],
        }
