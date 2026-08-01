"""Sprint 277 - Desktop Monitoring test."""
import unittest

from sam.desktop_runtime.monitoring.desktop_health import DesktopHealth
from sam.desktop_runtime.monitoring.desktop_metrics import DesktopMetrics
from sam.desktop_runtime.monitoring.desktop_monitor import DesktopMonitor
from sam.desktop_runtime.monitoring.desktop_report import DesktopReport
from sam.desktop_runtime.monitoring.desktop_snapshot import DesktopSnapshot
from sam.desktop_runtime.runtime.desktop_pipeline import DesktopPipeline


class TestDesktopHealth(unittest.TestCase):
    def test_health_default(self):
        h = DesktopHealth()
        self.assertEqual(h.status, "healthy")
        self.assertTrue(h.is_healthy())

    def test_health_immutable(self):
        h = DesktopHealth()
        with self.assertRaises(Exception):
            h.status = "offline"

    def test_health_with_check(self):
        h = DesktopHealth().with_check("foundation")
        self.assertIn("foundation", h.checks)

    def test_health_degraded(self):
        h = DesktopHealth(status="degraded")
        self.assertFalse(h.is_healthy())

    def test_health_as_dict(self):
        h = DesktopHealth().with_check("panels")
        self.assertEqual(h.as_dict()["checks"], ["panels"])


class TestDesktopMetrics(unittest.TestCase):
    def test_metrics_defaults(self):
        m = DesktopMetrics()
        self.assertEqual(m.panels_total, 0)
        self.assertEqual(m.cards_total, 0)

    def test_metrics_immutable(self):
        m = DesktopMetrics()
        with self.assertRaises(Exception):
            m.panels_total = 5

    def test_metrics_with_metric(self):
        m = DesktopMetrics().with_metric("panels", 10)
        self.assertEqual(m.metrics["panels"], 10)

    def test_metrics_with_metric_immutable(self):
        base = DesktopMetrics()
        base.with_metric("panels", 10)
        self.assertEqual(base.metrics, {})

    def test_metrics_as_dict(self):
        m = DesktopMetrics(panels_total=5, cards_total=3)
        dd = m.as_dict()
        self.assertEqual(dd["panels_total"], 5)
        self.assertEqual(dd["cards_total"], 3)


class TestDesktopSnapshot(unittest.TestCase):
    def test_snapshot_defaults(self):
        s = DesktopSnapshot()
        self.assertEqual(s.runtime, "desktop_runtime")
        self.assertEqual(s.version, "29.0.0")
        self.assertEqual(s.status, "idle")

    def test_snapshot_immutable(self):
        s = DesktopSnapshot()
        with self.assertRaises(Exception):
            s.status = "ready"

    def test_snapshot_with_status(self):
        s = DesktopSnapshot().with_status("ready")
        self.assertEqual(s.status, "ready")
        self.assertEqual(DesktopSnapshot().status, "idle")

    def test_snapshot_as_dict(self):
        s = DesktopSnapshot(panels=("Mission",))
        self.assertEqual(s.as_dict()["panels"], ["Mission"])


class TestDesktopReport(unittest.TestCase):
    def test_report_defaults(self):
        r = DesktopReport()
        self.assertEqual(r.status, "ok")
        self.assertEqual(r.observations, ())

    def test_report_immutable(self):
        r = DesktopReport()
        with self.assertRaises(Exception):
            r.status = "warn"

    def test_report_with_observation(self):
        r = DesktopReport().with_observation("all good")
        self.assertIn("all good", r.observations)

    def test_report_as_dict(self):
        r = DesktopReport().with_observation("x")
        dd = r.as_dict()
        self.assertEqual(dd["observations"], ["x"])
        self.assertEqual(dd["status"], "ok")


class TestDesktopMonitor(unittest.TestCase):
    def test_check_healthy(self):
        h = DesktopMonitor.check(DesktopPipeline())
        self.assertTrue(h.is_healthy())

    def test_check_has_stages(self):
        h = DesktopMonitor.check(DesktopPipeline())
        self.assertGreaterEqual(len(h.checks), 8)

    def test_snapshot(self):
        s = DesktopMonitor.snapshot(("Mission", "Runtime"))
        self.assertEqual(s.status, "ready")
        self.assertEqual(s.panels, ("Mission", "Runtime"))

    def test_report_from_health(self):
        r = DesktopMonitor.report(DesktopHealth())
        self.assertEqual(r.status, "healthy")
        self.assertEqual(r.counters["healthy"], 1)

    def test_report_degraded(self):
        r = DesktopMonitor.report(DesktopHealth(status="degraded"))
        self.assertEqual(r.counters["healthy"], 0)


if __name__ == "__main__":
    unittest.main()
