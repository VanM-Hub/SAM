"""M14-014/015 tests — Safety Certification + Operational Certification.

Memastikan:
  - Safety: FAIL mana pun -> all_pass=False (haram produksi autonomous).
  - Operational: tidak mengklaim PROVEN tanpa real E2E; operational_ready
    hanya bila >=1 real dan tidak ada unverified.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


from sam.delegated_authority.safety_certification import AutonomousSafetyCertifier
from sam.delegated_authority.operational_certification import (
    OperationalCertifier, CapabilityStatus,
)


class TestSafetyCertification:
    def test_clean_wiring_passes(self):
        ev = AutonomousSafetyCertifier.default_evidence()
        cert = AutonomousSafetyCertifier().certify(ev)
        assert cert.all_pass is True

    def test_violation_fails(self):
        ev = AutonomousSafetyCertifier.default_evidence()
        ev["evidence.single_canonical_executor"] = False   # second executor
        cert = AutonomousSafetyCertifier().certify(ev)
        assert cert.all_pass is False
        s2 = next(c for c in cert.checks if c.code == "S6")
        assert s2.verdict == "FAIL"

    def test_no_fake_success_rule_present(self):
        ev = AutonomousSafetyCertifier.default_evidence()
        cert = AutonomousSafetyCertifier().certify(ev)
        codes = [c.code for c in cert.checks]
        assert "S8" in codes          # independent verification wajib


class TestOperationalCertification:
    def test_not_ready_without_real(self):
        cert = OperationalCertifier.certify([
            CapabilityStatus("M14-001", "A", "unit"),
            CapabilityStatus("M14-007", "B", "unit"),
        ])
        assert cert.operational_ready is False
        assert cert.real_count == 0

    def test_not_ready_with_unverified(self):
        cert = OperationalCertifier.certify([
            CapabilityStatus("M14-007", "Provider", "real"),
            CapabilityStatus("M14-010", "PC", "unverified"),
        ])
        assert cert.operational_ready is False
        assert cert.unverified_count == 1

    def test_ready_with_real_and_no_unverified(self):
        cert = OperationalCertifier.certify([
            CapabilityStatus("M14-007", "Provider", "real"),
            CapabilityStatus("M14-009", "OpenClaw", "unit"),
            CapabilityStatus("M14-010", "PC", "blocked", "pending env"),
        ])
        assert cert.operational_ready is True
        assert cert.real_count == 1
        assert cert.blocked_count == 1

    def test_known_status_honest(self):
        cert = OperationalCertifier.m14_known_status(real_targets={})
        # tidak ada real -> operational_ready False (jangan klaim berlebihan)
        assert cert.real_count == 0
        assert cert.operational_ready is False
