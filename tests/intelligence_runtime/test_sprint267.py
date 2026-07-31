"""Sprint 267 - Certification (7 dimensi) test."""
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


class TestDimensions(unittest.TestCase):
    def test_7_dimensions(self):
        self.assertEqual(len(DIMENSIONS), 7)
        for d in ("Structure", "Integrity", "Consistency", "Completeness",
                  "Determinism", "Immutability", "RuntimeCoverage"):
            self.assertIn(d, DIMENSIONS)


class TestCertificationValidator(unittest.TestCase):
    def test_all_pass(self):
        v = CertificationValidator()
        ok, failed = v.validate(FULL)
        self.assertTrue(ok)
        self.assertEqual(failed, ())

    def test_missing_dimension(self):
        v = CertificationValidator()
        partial = {d: True for d in DIMENSIONS if d != "Determinism"}
        ok, failed = v.validate(partial)
        self.assertFalse(ok)
        self.assertIn("Determinism", failed)

    def test_failed_dimension(self):
        v = CertificationValidator()
        res = dict(FULL)
        res["Immutability"] = False
        ok, failed = v.validate(res)
        self.assertFalse(ok)
        self.assertIn("Immutability", failed)


class TestCertificationScore(unittest.TestCase):
    def test_from_results(self):
        s = CertificationScore.from_results(FULL)
        self.assertEqual(s.passed, 7)
        self.assertEqual(s.total, 7)
        self.assertAlmostEqual(s.ratio, 1.0)

    def test_partial_ratio(self):
        s = CertificationScore.from_results({"A": True, "B": False})
        self.assertEqual(s.passed, 1)
        self.assertEqual(s.total, 2)
        self.assertAlmostEqual(s.ratio, 0.5)


class TestCertificationManifest(unittest.TestCase):
    def test_default_pending(self):
        m = CertificationManifest()
        self.assertEqual(m.status, "pending")
        self.assertEqual(m.version, "28.0.0")


class TestCertifier(unittest.TestCase):
    def test_certify_all(self):
        c = Certifier()
        score, failed, manifest = c.certify(FULL)
        self.assertEqual(score.passed, 7)
        self.assertEqual(failed, ())
        self.assertEqual(manifest.status, "certified")

    def test_certify_default_all_true(self):
        c = Certifier()
        score, _, manifest = c.certify()
        self.assertEqual(score.passed, 7)
        self.assertEqual(manifest.status, "certified")

    def test_certify_failure(self):
        c = Certifier()
        res = dict(FULL)
        res["Structure"] = False
        score, failed, manifest = c.certify(res)
        self.assertEqual(score.passed, 6)
        self.assertIn("Structure", failed)
        self.assertEqual(manifest.status, "failed")


class TestCertificationReport(unittest.TestCase):
    def test_report(self):
        r = CertificationReport().build(FULL)
        self.assertEqual(r["score"]["passed"], 7)
        self.assertEqual(r["manifest"]["status"], "certified")
        self.assertEqual(r["failed"], [])


if __name__ == "__main__":
    unittest.main()
