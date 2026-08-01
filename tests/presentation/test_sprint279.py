"""Sprint 279 - Desktop Integration test."""
import unittest

from sam.presentation.conversation.bridge import ConversationBridge
from sam.presentation.dashboard_bridge.bridge import DashboardBridge
from sam.presentation.foundation import PresentationContract
from sam.presentation.integration.presentation_integ_manifest import (
    PresentationIntegManifest,
)
from sam.presentation.integration.presentation_integration_pipeline import (
    PresentationIntegrationPipeline,
    PresentationIntegrationResult,
)
from sam.presentation.presentation_layer import PresentationLayer
from sam.presentation.viewmodels.presentation_summary import PresentationSummary


class TestDesktopIntegManifest(unittest.TestCase):
    def test_manifest_runtime(self):
        m = PresentationIntegManifest()
        self.assertEqual(m.runtime, "presentation")
        self.assertEqual(m.version, "29.0.0")

    def test_manifest_pipeline_order(self):
        m = PresentationIntegManifest()
        self.assertEqual(
            list(m.pipeline),
            ["mission_runtime", "runtime_kernel", "execution_runtime", "dashboard"],
        )

    def test_manifest_immutable(self):
        m = PresentationIntegManifest()
        with self.assertRaises(Exception):
            m.runtime = "x"

    def test_manifest_as_dict(self):
        m = PresentationIntegManifest()
        self.assertIn("mission_runtime", m.as_dict()["pipeline"])

    def test_manifest_always_visualization(self):
        # pipeline integrasi hanya visualisasi, tidak mengeksekusi diri
        self.assertNotIn("execute", PresentationIntegManifest().pipeline)

    def test_manifest_source_runtime_first(self):
        m = PresentationIntegManifest()
        self.assertEqual(m.pipeline[0], "mission_runtime")

    def test_manifest_no_subsystem_write(self):
        for stage in PresentationIntegManifest().pipeline:
            self.assertFalse(stage.endswith("_service"))


class TestDesktopIntegrationResult(unittest.TestCase):
    def test_result_fields(self):
        r = PresentationIntegrationResult(
            summary=PresentationSummary(),
            health=None,
            cert_report=None,
        )
        self.assertTrue(r.preview_only)

    def test_result_immutable(self):
        r = PresentationIntegrationResult(summary=PresentationSummary(), health=None, cert_report=None)
        with self.assertRaises(Exception):
            r.preview_only = False

    def test_result_as_dict(self):
        r = PresentationIntegrationResult(summary=PresentationSummary(), health=None, cert_report=None)
        dd = r.as_dict()
        self.assertTrue(dd["preview_only"])
        self.assertEqual(dd["summary"]["version"], "29.0.0")


class TestDesktopIntegrationPipeline(unittest.TestCase):
    def _result(self):
        return PresentationIntegrationPipeline.run(
            runtime=PresentationLayer(),
            contract=PresentationContract(),
            conversation=ConversationBridge(),
            dashboard=DashboardBridge(),
        )

    def test_run_returns_result(self):
        r = self._result()
        self.assertIsInstance(r, PresentationIntegrationResult)

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
        self.assertTrue(PresentationIntegrationPipeline.certified(r))

    def test_certified_false_on_bad_bridge(self):
        class FakeBridge:
            def read_only(self):
                return False

        result = PresentationIntegrationPipeline.run(
            runtime=PresentationLayer(),
            contract=PresentationContract(),
            conversation=FakeBridge(),
            dashboard=FakeBridge(),
        )
        self.assertFalse(PresentationIntegrationPipeline.certified(result))

    def test_run_preview_only(self):
        r = self._result()
        self.assertTrue(r.preview_only)

    def test_as_dict_preview(self):
        r = self._result()
        dd = r.as_dict()
        self.assertEqual(len(dd["summary"]["panels"]), 10)

    def test_run_no_io(self):
        self.assertTrue(callable(PresentationIntegrationPipeline.run))

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
