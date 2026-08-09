"""Test IP-5.1-005 - AI Certification (MISSION-5.1).

Coverage: WP-41..WP-50 - provider, model, conversation, context, reasoning,
security, governance, regression, production readiness, mission certification.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.universal_ai import AICertification, CertStatus, VerificationArea


class TestAICertification:
    def test_full_certification_certified(self):
        cert = AICertification()
        cert.provider_certification()
        cert.model_certification()
        cert.conversation_certification()
        cert.context_certification()
        cert.reasoning_certification()
        cert.security_verification()
        cert.governance_verification()
        cert.regression_verification()
        cert.production_readiness()
        cert.mission_certification()
        result = cert.certify()
        assert result["certified"] is True
        assert result["status"] == CertStatus.CERTIFIED.value
        assert result["passed"] is True

    def test_not_certified_on_failure(self):
        cert = AICertification()
        # beberapa kegagalan -> NOT_CERTIFIED
        cert.security_verification(no_leakage=False, credential_isolation=False, provider_auth=False)
        cert.governance_verification(no_approval_by_ai=False)
        result = cert.certify()
        assert result["certified"] is False
        assert result["status"] == CertStatus.NOT_CERTIFIED.value

    def test_insufficient_evidence(self):
        cert = AICertification()
        result = cert.certify()
        assert result["status"] == CertStatus.INSUFFICIENT_EVIDENCE.value

    def test_conditional_on_minor_failures(self):
        cert = AICertification()
        cert.provider_certification()
        cert.model_certification()
        cert.conversation_certification()
        cert.context_certification()
        cert.reasoning_certification()
        cert.security_verification(no_leakage=False)  # 1 failure
        cert.governance_verification()
        cert.regression_verification()
        cert.production_readiness()
        cert.mission_certification()
        result = cert.certify()
        assert result["status"] == CertStatus.CONDITIONALLY_CERTIFIED.value

    def test_evidence_areas_present(self):
        cert = AICertification()
        cert.provider_certification()
        cert.governance_verification()
        areas = {e.area for e in cert.result().evidences}
        assert VerificationArea.PROVIDER in areas
        assert VerificationArea.GOVERNANCE in areas
