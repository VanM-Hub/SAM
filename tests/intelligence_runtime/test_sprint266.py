"""Sprint 266 - Monitoring test."""
import unittest

from sam.intelligence_runtime.health import RuntimeHealth
from sam.intelligence_runtime.history import RuntimeHistory
from sam.intelligence_runtime.metrics import RuntimeMetrics
from sam.intelligence_runtime.monitor import RuntimeMonitor
from sam.intelligence_runtime.snapshot import RuntimeSnapshot


class TestRuntimeMetrics(unittest.TestCase):
    def test_counter(self):
        m = RuntimeMetrics().with_counter("contexts_built")
        m2 = m.with_counter("contexts_built")
        self.assertEqual(m2.get("contexts_built"), 2)
        # original tak berubah
        self.assertEqual(m.get("contexts_built"), 1)

    def test_immutable(self):
        m = RuntimeMetrics()
        with self.assertRaises(Exception):
            m.counters = {}

    def test_as_dict(self):
        m = RuntimeMetrics().with_counter("x")
        d = m.as_dict()
        self.assertEqual(d["counters"]["x"], 1)


class TestRuntimeHealth(unittest.TestCase):
    def test_default(self):
        h = RuntimeHealth()
        self.assertTrue(h.healthy)
        self.assertEqual(h.message, "ok")


class TestRuntimeSnapshot(unittest.TestCase):
    def test_snapshot(self):
        s = RuntimeSnapshot()
        d = s.as_dict()
        self.assertTrue(d["health"]["healthy"])
        self.assertEqual(d["metrics"]["counters"], {})


class TestRuntimeHistory(unittest.TestCase):
    def test_record_append_only(self):
        h = RuntimeHistory()
        h2 = h.record(RuntimeMetrics().with_counter("a"))
        # original kosong
        self.assertEqual(len(h), 0)
        self.assertEqual(len(h2), 1)
        self.assertEqual(h2.last().get("a"), 1)

    def test_empty_last(self):
        h = RuntimeHistory()
        self.assertEqual(h.last().get("nope"), 0)


class TestRuntimeMonitor(unittest.TestCase):
    def test_snapshot(self):
        mon = RuntimeMonitor()
        s = mon.snapshot(healthy=True)
        self.assertTrue(s.as_dict()["health"]["healthy"])

    def test_snapshot_with_metrics(self):
        mon = RuntimeMonitor()
        m = RuntimeMetrics().with_counter("calls", 7)
        s = mon.snapshot_with(metrics=m)
        self.assertEqual(s.as_dict()["metrics"]["counters"]["calls"], 7)


if __name__ == "__main__":
    unittest.main()
