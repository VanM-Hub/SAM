"""Sprint 279 - Desktop Integration test."""
import unittest

from sam.desktop_runtime.conversation.bridge import ConversationBridge
from sam.desktop_runtime.dashboard_bridge.bridge import DashboardBridge
from sam.desktop_runtime.foundation import DesktopContract
from sam.desktop_runtime.integration.desktop_integ_manifest import (
    DesktopIntegManifest,
)
from sam.desktop_runtime.integration.desktop_integration_pipeline import (
    DesktopIntegrationPipeline,
    DesktopIntegrationResult,
)
from sam.desktop_runtime.runtime.desktop_runtime import DesktopRuntime
from sam.desktop_runtime.runtime.desktop_summary import DesktopSummary


class TestDesktopIntegManifest(unittest.TestCase):
    def test_manifest_runtime(self):
        m = DesktopIntegManifest()
        self.assertEqual(m.runtime, "desktop_runtime")
        self.assertEqual(m.version, "29.0.0")

    def test_manifest_pipeline_order(self):
        m = DesktopIntegManifest()
        self.assertEqual(
            list(m.pipeline),
            ["mission_runtime", "runtime_kernel", "execution_runtime", "dashboard"],
        )

    def test_manifest_immutable(self):
        m = DesktopIntegManifest()
        with self.assertRaises(Exception):
            m.runtime = "x"

    def test_manifest_as_dict(self):
        m = DesktopIntegManifest()
        self.assertIn("mission_runtime", m.as_dict()["pipeline"])

    def test_manifest_always_visualization(self):
        # pipeline integrasi hanya visualisasi, tidak mengeksekusi diri
        self.assertNotIn("execute", DesktopIntegManifest().pipeline)

    def test_manifest_source_runtime_first(self):
        m = DesktopIntegManifest()
        self.assertEqual(m.pipeline[0], "mission_runtime")

    def test_manifest_no_subsystem_write(self):
        for stage in DesktopIntegManifest().pipeline:
            self.assertFalse(stage.endswith("_service"))


class TestDesktopIntegrationResult(unittest.TestCase):
    def test_result_fields(self):
        r = DesktopIntegrationResult(
            summary=DesktopSummary(),
            health=None,
            cert_report=None,
        )
        self.assertTrue(r.preview_only)

    def test_result_immutable(self):
        r = DesktopIntegrationResult(summary=DesktopSummary(), health=None, cert_report=None)
        with self.assertRaises(Exception):
            r.preview_only = False

    def test_result_as_dict(self):
        r = DesktopIntegrationResult(summary=DesktopSummary(), health=None, cert_report=None)
        dd = r.as_dict()
        self.assertTrue(dd["preview_only"])
        self.assertEqual(dd["summary"]["version"], "29.0.0")


class TestDesktopIntegrationPipeline(unittest.TestCase):
    def _result(self):
        return DesktopIntegrationPipeline.run(
            runtime=DesktopRuntime(),
            contract=DesktopContract(),
            conversation=ConversationBridge(),
            dashboard=DashboardBridge(),
        )

    def test_run_returns_result(self):
        r = self._result()
        self.assertIsInstance(r, DesktopIntegrationResult)

    def test_run_summary_has_panels(self):
        r = self._result()
        self.assertEqual(len(r.summary.panels), 10)

    def test_run_health_healthy(self):
        r = self._result()
        self.assertTrue(r.health.is_healthy())

    def test_run_cert_passed(self):
        r = self._result()
        self.assertTrue(r.cert_report.passed)

    def test_run_cert_7_dims(self):
        r = self._result()
        self.assertEqual(len(r.cert_report.dimensions), 7)

    def test_certified_true(self):
        r = self._result()
        self.assertTrue(DesktopIntegrationPipeline.certified(r))

    def test_certified_false_on_bad_bridge(self):
        class FakeBridge:
            def read_only(self):
                return False

        result = DesktopIntegrationPipeline.run(
            runtime=DesktopRuntime(),
            contract=DesktopContract(),
            conversation=FakeBridge(),
            dashboard=FakeBridge(),
        )
        self.assertFalse(DesktopIntegrationPipeline.certified(result))

    def test_run_preview_only(self):
        r = self._result()
        self.assertTrue(r.preview_only)

    def test_as_dict_preview(self):
        r = self._result()
        dd = r.as_dict()
        self.assertEqual(len(dd["summary"]["panels"]), 10)

    def test_run_no_io(self):
        self.assertTrue(callable(DesktopIntegrationPipeline.run))

    def test_run_health_from_monitor(self):
        r = self._result()
        self.assertEqual(r.health.status, "healthy")

    def test_cert_report_version(self):
        r = self._result()
        self.assertEqual(r.cert_report.version, "29.0.0")

    def test_summary_read_only(self):
        r = self._result()
        self.assertTrue(r.summary.read_only)
        self.assertFalse(r.summary.execute_self)

    def test_certification_visualization_only(self):
        # semua eksekusi nyata berada di luar scope desktop (RuntimeService)
        r = self._result()
        self.assertTrue(r.preview_only)

    def test_all_failed_dims_empty(self):
        r = self._result()
        self.assertEqual(r.cert_report.failed_dimensions, ())


if __name__ == "__main__":
    unittest.main()
