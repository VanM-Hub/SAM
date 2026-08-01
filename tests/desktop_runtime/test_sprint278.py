"""Sprint 278 - Desktop Certification test."""
import unittest

from sam.desktop_runtime.certification import (
    CertificationDimension,
    DesktopCertManifest,
    DesktopCertReport,
    DesktopCertifier,
)
from sam.desktop_runtime.conversation.bridge import ConversationBridge
from sam.desktop_runtime.dashboard_bridge.bridge import DashboardBridge
from sam.desktop_runtime.foundation import DesktopContract
from sam.desktop_runtime.runtime.desktop_runtime import DesktopRuntime


def default_runtime():
    return DesktopRuntime()


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
        m = DesktopCertManifest()
        self.assertEqual(m.program, "F")
        self.assertEqual(m.version, "29.0.0")

    def test_manifest_7_dimensions(self):
        m = DesktopCertManifest()
        self.assertEqual(len(m.dimensions), 7)

    def test_manifest_required_dims(self):
        m = DesktopCertManifest()
        for dim in ("composition_only", "preview_only", "deterministic_sync",
                    "no_execute_self", "immutable_dto", "readonly_bridges",
                    "no_llm_inference"):
            self.assertIn(dim, m.dimensions)

    def test_manifest_immutable(self):
        m = DesktopCertManifest()
        with self.assertRaises(Exception):
            m.dimensions = ()

    def test_manifest_as_dict(self):
        m = DesktopCertManifest()
        self.assertEqual(len(m.as_dict()["dimensions"]), 7)


class TestDesktopCertReport(unittest.TestCase):
    def test_report_from_list(self):
        dims = [CertificationDimension("a", True), CertificationDimension("b", True)]
        r = DesktopCertReport.from_list(dims)
        self.assertTrue(r.passed)

    def test_report_failed(self):
        dims = [CertificationDimension("a", True), CertificationDimension("b", False)]
        r = DesktopCertReport.from_list(dims)
        self.assertFalse(r.passed)
        self.assertEqual(r.failed_dimensions, ("b",))

    def test_report_empty(self):
        r = DesktopCertReport.from_list([])
        self.assertTrue(r.passed)

    def test_report_immutable(self):
        r = DesktopCertReport.from_list([])
        with self.assertRaises(Exception):
            r.runtime = "x"

    def test_report_as_dict(self):
        r = DesktopCertReport.from_list([CertificationDimension("a", True)])
        dd = r.as_dict()
        self.assertIn("dimensions", dd)
        self.assertEqual(dd["failed_dimensions"], [])


class TestDesktopCertifier(unittest.TestCase):
    def _validate(self):
        return DesktopCertifier.validate_desktop(
            runtime=default_runtime(),
            contract=DesktopContract(),
            conversation=ConversationBridge(),
            dashboard=DashboardBridge(),
        )

    def test_7_dimensions_checked(self):
        self.assertEqual(len(self._validate()), 7)

    def test_all_passed(self):
        self.assertTrue(DesktopCertifier.all_passed(self._validate()))

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

        dims = DesktopCertifier.validate_desktop(
            runtime=default_runtime(),
            contract=DesktopContract(),
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

        dims = DesktopCertifier.validate_desktop(
            runtime=default_runtime(),
            contract=DesktopContract(),
            conversation=FakeBridge(),
            dashboard=FakeBridge(),
        )
        self.assertFalse(DesktopCertifier.all_passed(dims))


if __name__ == "__main__":
    unittest.main()
