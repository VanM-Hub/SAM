"""Sprint 277 - Desktop Monitoring test."""
import unittest

from sam.presentation.monitoring.presentation_health import PresentationHealth
from sam.presentation.monitoring.presentation_metrics import PresentationMetrics
from sam.presentation.monitoring.presentation_monitor import PresentationMonitor
from sam.presentation.monitoring.presentation_report import PresentationReport
from sam.presentation.monitoring.presentation_snapshot import PresentationSnapshot
from sam.presentation.composition.presentation_pipeline import PresentationPipeline


class TestDesktopHealth(unittest.TestCase):
    def test_health_default(self):
        h = PresentationHealth()
        self.assertEqual(h.status, "healthy")
        self.assertTrue(h.is_healthy())

    def test_health_immutable(self):
        h = PresentationHealth()
        with self.assertRaises(Exception):
            h.status = "offline"

    def test_health_with_check(self):
        h = PresentationHealth().with_check("foundation")
        self.assertIn("foundation", h.checks)

    def test_health_degraded(self):
        h = PresentationHealth(status="degraded")
        self.assertFalse(h.is_healthy())

    def test_health_as_dict(self):
        h = PresentationHealth().with_check("panels")
        self.assertEqual(h.as_dict()["checks"], ["panels"])


class TestDesktopMetrics(unittest.TestCase):
    def test_metrics_defaults(self):
        m = PresentationMetrics()
        self.assertEqual(m.panels_total, 0)
        self.assertEqual(m.cards_total, 0)

    def test_metrics_immutable(self):
        m = PresentationMetrics()
        with self.assertRaises(Exception):
            m.panels_total = 5

    def test_metrics_with_metric(self):
        m = PresentationMetrics().with_metric("panels", 10)
        self.assertEqual(m.metrics["panels"], 10)

    def test_metrics_with_metric_immutable(self):
        base = PresentationMetrics()
        base.with_metric("panels", 10)
        self.assertEqual(base.metrics, {})

    def test_metrics_as_dict(self):
        m = PresentationMetrics(panels_total=5, cards_total=3)
        dd = m.as_dict()
        self.assertEqual(dd["panels_total"], 5)
        self.assertEqual(dd["cards_total"], 3)


class TestDesktopSnapshot(unittest.TestCase):
    def test_snapshot_defaults(self):
        s = PresentationSnapshot()
        self.assertEqual(s.runtime, "presentation")
        self.assertEqual(s.version, "29.0.0")
        self.assertEqual(s.status, "idle")

    def test_snapshot_immutable(self):
        s = PresentationSnapshot()
        with self.assertRaises(Exception):
            s.status = "ready"

    def test_snapshot_with_status(self):
        s = PresentationSnapshot().with_status("ready")
        self.assertEqual(s.status, "ready")
        self.assertEqual(PresentationSnapshot().status, "idle")

    def test_snapshot_as_dict(self):
        s = PresentationSnapshot(panels=("Mission",))
        self.assertEqual(s.as_dict()["panels"], ["Mission"])


class TestDesktopReport(unittest.TestCase):
    def test_report_defaults(self):
        r = PresentationReport()
        self.assertEqual(r.status, "ok")
        self.assertEqual(r.observations, ())

    def test_report_immutable(self):
        r = PresentationReport()
        with self.assertRaises(Exception):
            r.status = "warn"

    def test_report_with_observation(self):
        r = PresentationReport().with_observation("all good")
        self.assertIn("all good", r.observations)

    def test_report_as_dict(self):
        r = PresentationReport().with_observation("x")
        dd = r.as_dict()
        self.assertEqual(dd["observations"], ["x"])
        self.assertEqual(dd["status"], "ok")


class TestDesktopMonitor(unittest.TestCase):
    def test_check_healthy(self):
        h = PresentationMonitor.check(PresentationPipeline())
        self.assertTrue(h.is_healthy())

    def test_check_has_stages(self):
        h = PresentationMonitor.check(PresentationPipeline())
        self.assertGreaterEqual(len(h.checks), 8)

    def test_snapshot(self):
        s = PresentationMonitor.snapshot(("Mission", "Runtime"))
        self.assertEqual(s.status, "ready")
        self.assertEqual(s.panels, ("Mission", "Runtime"))

    def test_report_from_health(self):
        r = PresentationMonitor.report(PresentationHealth())
        self.assertEqual(r.status, "healthy")
        self.assertEqual(r.counters["healthy"], 1)

    def test_report_degraded(self):
        r = PresentationMonitor.report(PresentationHealth(status="degraded"))
        self.assertEqual(r.counters["healthy"], 0)


if __name__ == "__main__":
    unittest.main()
