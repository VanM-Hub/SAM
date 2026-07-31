"""Sprint 266 - Monitoring: test lanjutan."""
import unittest

from sam.intelligence_runtime.health import RuntimeHealth
from sam.intelligence_runtime.history import RuntimeHistory
from sam.intelligence_runtime.metrics import RuntimeMetrics
from sam.intelligence_runtime.monitor import RuntimeMonitor
from sam.intelligence_runtime.snapshot import RuntimeSnapshot


class TestMetricsBehavior(unittest.TestCase):
    def test_multiple_counters(self):
        m = (RuntimeMetrics()
             .with_counter("a")
             .with_counter("b")
             .with_counter("a"))
        self.assertEqual(m.get("a"), 2)
        self.assertEqual(m.get("b"), 1)

    def test_missing_counter_zero(self):
        self.assertEqual(RuntimeMetrics().get("nope"), 0)

    def test_with_counter_custom_value(self):
        m = RuntimeMetrics().with_counter("calls", 5)
        self.assertEqual(m.get("calls"), 5)

    def test_immutable_counters_attr_reassign(self):
        m = RuntimeMetrics(counters={"x": 1})
        with self.assertRaises(Exception):
            m.counters = {}  # frozen -> reassign ditolak

    def test_frozen_prevents_attr_reassign(self):
        m = RuntimeMetrics()
        with self.assertRaises(Exception):
            m.counters = {"x": 1}


class TestHealthBehavior(unittest.TestCase):
    def test_unhealthy(self):
        h = RuntimeHealth(healthy=False, message="down")
        self.assertFalse(h.healthy)
        self.assertEqual(h.message, "down")

    def test_as_dict(self):
        d = RuntimeHealth().as_dict()
        self.assertEqual(d, {"healthy": True, "message": "ok"})


class TestSnapshotBehavior(unittest.TestCase):
    def test_custom_health(self):
        s = RuntimeSnapshot(health=RuntimeHealth(healthy=False))
        self.assertFalse(s.as_dict()["health"]["healthy"])

    def test_custom_meta(self):
        s = RuntimeSnapshot(meta={"runtime": "intelligence"})
        self.assertEqual(s.as_dict()["meta"]["runtime"], "intelligence")


class TestHistoryBehavior(unittest.TestCase):
    def test_multiple_records(self):
        h = RuntimeHistory()
        h = h.record(RuntimeMetrics().with_counter("x"))
        h = h.record(RuntimeMetrics().with_counter("x"))
        self.assertEqual(len(h), 2)
        self.assertEqual(h.last().get("x"), 1)

    def test_entries_order(self):
        m1 = RuntimeMetrics().with_counter("step", 1)
        m2 = RuntimeMetrics().with_counter("step", 2)
        h = RuntimeHistory().record(m1).record(m2)
        self.assertEqual(h.entries[0].as_dict()["counters"]["step"], 1)
        self.assertEqual(h.entries[1].as_dict()["counters"]["step"], 2)


class TestMonitorBehavior(unittest.TestCase):
    def test_unhealthy_snapshot(self):
        mon = RuntimeMonitor()
        s = mon.snapshot(healthy=False, message="degraded")
        self.assertFalse(s.as_dict()["health"]["healthy"])
        self.assertEqual(s.as_dict()["health"]["message"], "degraded")

    def test_snapshot_meta_mode(self):
        mon = RuntimeMonitor()
        self.assertEqual(mon.snapshot().as_dict()["meta"]["mode"], "preview")


if __name__ == "__main__":
    unittest.main()
