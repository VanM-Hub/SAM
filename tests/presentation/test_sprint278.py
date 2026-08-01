"""Sprint 278 - Desktop Certification test."""
import unittest

from sam.presentation.certification import (
    CertificationDimension,
    PresentationCertManifest,
    PresentationCertReport,
    PresentationCertifier,
)
from sam.presentation.conversation.bridge import ConversationBridge
from sam.presentation.dashboard_bridge.bridge import DashboardBridge
from sam.presentation.foundation import PresentationContract
from sam.presentation.presentation_layer import PresentationLayer


def default_runtime():
    return PresentationLayer()


class TestCertificationDimension(unittest.TestCase):
    def test_dimension_defaults(self):
        d = CertificationDimension(name="x", passed=True)
        self.assertEqual(d.name, "x")
        self.assertTrue(d.passed)
        self.assertEqual(d.detail, "")

    def test_dimension_immutable(self):
        d = CertificationDimension(name="x", passed=True)
        with self.assertRaises(Exception):
            d.passed = False

    def test_dimension_as_dict(self):
        d = CertificationDimension(name="x", passed=True, detail="ok")
        dd = d.as_dict()
        self.assertEqual(dd["name"], "x")
        self.assertEqual(dd["detail"], "ok")


class TestDesktopCertManifest(unittest.TestCase):
    def test_manifest_program_f(self):
        m = PresentationCertManifest()
        self.assertEqual(m.program, "F")
        self.assertEqual(m.version, "29.0.0")

    def test_manifest_7_dimensions(self):
        m = PresentationCertManifest()
        self.assertEqual(len(m.dimensions), 7)

    def test_manifest_required_dims(self):
        m = PresentationCertManifest()
        for dim in ("composition_only", "preview_only", "deterministic_sync",
                    "no_execute_self", "immutable_dto", "readonly_bridges",
                    "no_llm_inference"):
            self.assertIn(dim, m.dimensions)

    def test_manifest_immutable(self):
        m = PresentationCertManifest()
        with self.assertRaises(Exception):
            m.dimensions = ()

    def test_manifest_as_dict(self):
        m = PresentationCertManifest()
        self.assertEqual(len(m.as_dict()["dimensions"]), 7)


class TestDesktopCertReport(unittest.TestCase):
    def test_report_from_list(self):
        dims = [CertificationDimension("a", True), CertificationDimension("b", True)]
        r = PresentationCertReport.from_list(dims)
        self.assertTrue(r.passed)

    def test_report_failed(self):
        dims = [CertificationDimension("a", True), CertificationDimension("b", False)]
        r = PresentationCertReport.from_list(dims)
        self.assertFalse(r.passed)
        self.assertEqual(r.failed_dimensions, ("b",))

    def test_report_empty(self):
        r = PresentationCertReport.from_list([])
        self.assertTrue(r.passed)

    def test_report_immutable(self):
        r = PresentationCertReport.from_list([])
        with self.assertRaises(Exception):
            r.runtime = "x"

    def test_report_as_dict(self):
        r = PresentationCertReport.from_list([CertificationDimension("a", True)])
        dd = r.as_dict()
        self.assertIn("dimensions", dd)
        self.assertEqual(dd["failed_dimensions"], [])


class TestDesktopCertifier(unittest.TestCase):
    def _validate(self):
        return PresentationCertifier.validate_desktop(
            runtime=default_runtime(),
            contract=PresentationContract(),
            conversation=ConversationBridge(),
            dashboard=DashboardBridge(),
        )

    def test_7_dimensions_checked(self):
        self.assertEqual(len(self._validate()), 7)

    def test_all_passed(self):
        self.assertTrue(PresentationCertifier.all_passed(self._validate()))

    def test_composition_dimension(self):
        dims = {d.name: d.passed for d in self._validate()}
        self.assertTrue(dims["composition_only"])

    def test_preview_dimension(self):
        dims = {d.name: d.passed for d in self._validate()}
        self.assertTrue(dims["preview_only"])

    def test_deterministic_dimension(self):
        dims = {d.name: d.passed for d in self._validate()}
        self.assertTrue(dims["deterministic_sync"])

    def test_no_execute_dimension(self):
        dims = {d.name: d.passed for d in self._validate()}
        self.assertTrue(dims["no_execute_self"])

    def test_immutable_dimension(self):
        dims = {d.name: d.passed for d in self._validate()}
        self.assertTrue(dims["immutable_dto"])

    def test_readonly_bridges_dimension(self):
        dims = {d.name: d.passed for d in self._validate()}
        self.assertTrue(dims["readonly_bridges"])

    def test_no_llm_dimension(self):
        dims = {d.name: d.passed for d in self._validate()}
        self.assertTrue(dims["no_llm_inference"])

    def test_false_bridge_fails_readonly(self):
        class FakeBridge:
            def read_only(self):
                return False

        dims = PresentationCertifier.validate_desktop(
            runtime=default_runtime(),
            contract=PresentationContract(),
            conversation=FakeBridge(),
            dashboard=FakeBridge(),
        )
        dimmap = {d.name: d.passed for d in dims}
        self.assertFalse(dimmap["readonly_bridges"])

    def test_dimension_names_exact(self):
        names = [d.name for d in self._validate()]
        self.assertEqual(
            names,
            [
                "composition_only",
                "preview_only",
                "deterministic_sync",
                "no_execute_self",
                "immutable_dto",
                "readonly_bridges",
                "no_llm_inference",
            ],
        )

    def test_all_passed_false_when_any_fail(self):
        class FakeBridge:
            def read_only(self):
                return False

        dims = PresentationCertifier.validate_desktop(
            runtime=default_runtime(),
            contract=PresentationContract(),
            conversation=FakeBridge(),
            dashboard=FakeBridge(),
        )
        self.assertFalse(PresentationCertifier.all_passed(dims))


if __name__ == "__main__":
    unittest.main()
