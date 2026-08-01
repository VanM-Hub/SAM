"""Sprint 275 - Desktop Dashboard test."""
import unittest

from sam.presentation.dashboard.card_model import DashboardCard
from sam.presentation.dashboard.dashboard_composer import DashboardComposer
from sam.presentation.dashboard.dashboard_layout import DashboardLayout
from sam.presentation.dashboard.dashboard_runtime import DashboardRuntime
from sam.presentation.dashboard.dashboard_snapshot import DashboardSnapshot


class TestDashboardCard(unittest.TestCase):
    def test_card_defaults(self):
        c = DashboardCard(title="Runtime")
        self.assertEqual(c.kind, "card")
        self.assertEqual(c.size, 1)
        self.assertEqual(c.sections, ())

    def test_card_immutable(self):
        c = DashboardCard(title="Runtime")
        with self.assertRaises(Exception):
            c.title = "x"

    def test_card_with_sections(self):
        c = DashboardCard(title="Runtime").with_sections("status", "health")
        self.assertEqual(c.sections, ("status", "health"))

    def test_card_as_dict(self):
        c = DashboardCard(title="Runtime", source_runtime="Runtime Kernel")
        dd = c.as_dict()
        self.assertEqual(dd["title"], "Runtime")
        self.assertEqual(dd["source_runtime"], "Runtime Kernel")


class TestDashboardComposer(unittest.TestCase):
    def test_compose_sorted(self):
        cards = (DashboardCard(title="Z"), DashboardCard(title="A"))
        ordered = DashboardComposer.compose(cards)
        self.assertEqual([c.title for c in ordered], ["A", "Z"])

    def test_compose_no_execute(self):
        cards = (DashboardCard(title="Runtime"),)
        out = DashboardComposer.compose(cards)
        self.assertEqual(len(out), 1)

    def test_compact_sizes(self):
        cards = (DashboardCard(title="A", size=2), DashboardCard(title="B", size=1))
        self.assertEqual(DashboardComposer.compact(cards), 3)

    def test_pick_selected(self):
        cards = (DashboardCard(title="A"), DashboardCard(title="B"))
        picked = DashboardComposer.pick(cards, "A")
        self.assertEqual([c.title for c in picked], ["A"])

    def test_pick_unordered(self):
        cards = (DashboardCard(title="A"), DashboardCard(title="B"))
        picked = DashboardComposer.pick(cards, "B", "A")
        self.assertEqual([c.title for c in picked], ["A", "B"])


class TestDashboardLayout(unittest.TestCase):
    def test_layout_default(self):
        l = DashboardLayout()
        self.assertEqual(l.name, "default")
        self.assertEqual(l.regions, {})

    def test_layout_with_region(self):
        l = DashboardLayout().with_region("main", 2)
        self.assertEqual(l.regions["main"], 2)
        self.assertIn("main", l.region_names)

    def test_layout_immutable(self):
        l = DashboardLayout().with_region("main")
        self.assertEqual(DashboardLayout().regions, {})

    def test_layout_as_dict(self):
        l = DashboardLayout().with_region("main", 2)
        self.assertEqual(l.as_dict()["regions"]["main"], 2)


class TestDashboardSnapshot(unittest.TestCase):
    def test_snapshot_default(self):
        s = DashboardSnapshot()
        self.assertEqual(s.dashboard_id, "main")
        self.assertEqual(s.total_size, 0)

    def test_snapshot_auto_total(self):
        cards = (DashboardCard(title="A", size=2), DashboardCard(title="B"))
        s = DashboardSnapshot(cards=cards)
        self.assertEqual(s.total_size, 3)

    def test_snapshot_immutable(self):
        s = DashboardSnapshot()
        with self.assertRaises(Exception):
            s.dashboard_id = "x"

    def test_snapshot_card_titles(self):
        s = DashboardSnapshot(cards=(DashboardCard(title="A"),))
        self.assertEqual(s.card_titles(), ("A",))

    def test_snapshot_as_dict(self):
        s = DashboardSnapshot(cards=(DashboardCard(title="A"),))
        dd = s.as_dict()
        self.assertEqual(len(dd["cards"]), 1)
        self.assertEqual(dd["total_size"], 1)


class TestDashboardRuntime(unittest.TestCase):
    def test_runtime_empty(self):
        r = DashboardRuntime()
        snap = r.run()
        self.assertEqual(snap.card_titles(), ())

    def test_runtime_composes_sorted(self):
        r = DashboardRuntime(
            cards=(DashboardCard(title="Z"), DashboardCard(title="A"))
        )
        snap = r.run()
        self.assertEqual(list(snap.card_titles()), ["A", "Z"])

    def test_runtime_immutable_after_init(self):
        r = DashboardRuntime()
        with self.assertRaises(Exception):
            r._cards = ()

    def test_runtime_as_dict(self):
        r = DashboardRuntime(cards=(DashboardCard(title="A"),))
        dd = r.as_dict()
        self.assertFalse(dd["execute_self"])
        self.assertTrue(dd["preview_only"])

    def test_runtime_no_io(self):
        r = DashboardRuntime()
        self.assertTrue(callable(r.run))

    def test_runtime_cards_readonly(self):
        cards = (DashboardCard(title="A"),)
        r = DashboardRuntime(cards=cards)
        self.assertEqual(len(r.cards), 1)


if __name__ == "__main__":
    unittest.main()
