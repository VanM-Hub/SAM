"""Sprint 267 - Certification: test lanjutan."""
import unittest

from sam.intelligence_runtime.certifier import Certifier
from sam.intelligence_runtime.manifest import CertificationManifest
from sam.intelligence_runtime.report import CertificationReport
from sam.intelligence_runtime.score import CertificationScore
from sam.intelligence_runtime.validator import (
    CertificationValidator,
    DIMENSIONS,
)


FULL = {d: True for d in DIMENSIONS}


class TestCertifierBehavior(unittest.TestCase):
    def test_certifier_immutable_fields(self):
        c = Certifier()
        self.assertEqual(c.validator.__class__.__name__, "CertificationValidator")

    def test_certify_returns_three(self):
        out = Certifier().certify(FULL)
        self.assertEqual(len(out), 3)

    def test_certify_explicit_results(self):
        res = {"Structure": True, "Integrity": False}
        score, failed, manifest = Certifier().certify(res)
        self.assertEqual(score.passed, 1)
        self.assertIn("Integrity", failed)


class TestCertificationReportBehavior(unittest.TestCase):
    def test_report_details(self):
        r = CertificationReport().build(
            FULL, details={"note": "intelligence"})
        self.assertEqual(r["details"]["note"], "intelligence")

    def test_report_no_details(self):
        r = CertificationReport().build(FULL)
        self.assertEqual(r["details"], {})


class TestCertificationManifestBehavior(unittest.TestCase):
    def test_manifest_custom(self):
        m = CertificationManifest(
            version="28.0.0", dimensions=("Structure",), status="failed")
        d = m.as_dict()
        self.assertEqual(d["dimensions"], ["Structure"])
        self.assertEqual(d["status"], "failed")


class TestCertificationScoreBehavior(unittest.TestCase):
    def test_zero_total_ratio(self):
        s = CertificationScore(passed=0, total=0)
        self.assertEqual(s.ratio, 0.0)

    def test_all_pass_ratio(self):
        s = CertificationScore.from_results(FULL)
        self.assertEqual(s.ratio, 1.0)

    def test_half_ratio(self):
        s = CertificationScore.from_results({"A": True, "B": False})
        self.assertAlmostEqual(s.ratio, 0.5)


class TestValidatorPure(unittest.TestCase):
    def test_validator_no_side_effect(self):
        v = CertificationValidator()
        res = dict(FULL)
        _ = v.validate(res)
        # input tidak berubah
        self.assertEqual(res, FULL)

    def test_dimensions_complete_set(self):
        self.assertIn("RuntimeCoverage", DIMENSIONS)
        self.assertNotIn("google", [d.lower() for d in DIMENSIONS])


if __name__ == "__main__":
    unittest.main()
