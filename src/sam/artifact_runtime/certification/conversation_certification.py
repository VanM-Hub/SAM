"""Conversation Certification Bridge — 5 read-only queries (Sprint 226)."""
from __future__ import annotations

from .artifact_certification import ArtifactCertification
from .artifact_score import ArtifactScorer
from .artifact_manifest_report import ArtifactManifestReporter
from .artifact_certification_report import ArtifactCertificationReporter
from .artifact_certification_validator import ArtifactCertificationValidator


class ConversationCertificationBridge:
    """Bridge conversation — 5 query sertifikasi artifact."""

    def __init__(self) -> None:
        self._scorer = ArtifactScorer()
        self._manifest = ArtifactManifestReporter()
        self._report = ArtifactCertificationReporter()
        self._validator = ArtifactCertificationValidator()

    def query_1_certify(self) -> dict:
        res = ArtifactCertification().certify()
        return {"certified": res.certified, "score": res.score}

    def query_2_score(self) -> dict:
        res = ArtifactCertification().certify()
        s = self._scorer.score(res)
        return {"score": s.score, "certified": s.certified}

    def query_3_manifest(self) -> dict:
        m = self._manifest.report(("mission", "agent", "artifact"))
        return {"integrated": m.integrated}

    def query_4_report(self) -> dict:
        r = self._report.report(True, 100.0)
        return {"certified": r.certified, "external_calls": r.external_calls}

    def query_5_validate(self) -> dict:
        res = ArtifactCertification().certify()
        v = self._validator.validate(res)
        return {"valid": v.valid}
