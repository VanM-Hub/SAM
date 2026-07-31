"""Sprint 264 - Context Assembly test."""
import unittest

from sam.intelligence_runtime.context_builder import (
    ContextBuilder,
    DEFAULT_SECTIONS,
)
from sam.intelligence_runtime.context_report import ContextReport
from sam.intelligence_runtime.context_snapshot import ContextSnapshot
from sam.intelligence_runtime.context_summary import ContextSummary
from sam.intelligence_runtime.context_validator import ContextValidator


SECTION_NAMES = (
    "Mission", "Agent", "Workflow", "Skill", "Memory", "Knowledge",
    "Policy", "Audit", "Artifact", "Model", "Provider", "Execution",
)


def build_full():
    b = ContextBuilder.create()
    for s in SECTION_NAMES:
        b = b.add(s, {"present": True})
    return b.build()


class TestContextSnapshot(unittest.TestCase):
    def test_immutable(self):
        s = ContextSnapshot()
        with self.assertRaises(Exception):
            s.sections = {}  # frozen

    def test_section_access(self):
        s = ContextSnapshot(sections={"Mission": {"id": "m1"}}, order=("Mission",))
        self.assertEqual(s.section("Mission"), {"id": "m1"})
        self.assertEqual(s.section("Bogus"), {})


class TestContextBuilder(unittest.TestCase):
    def test_build_full(self):
        snap = build_full()
        self.assertEqual(len(snap.sections), len(SECTION_NAMES))
        # urutan sesuai DEFAULT_SECTIONS
        self.assertEqual(list(snap.sections.keys()), list(DEFAULT_SECTIONS))

    def test_unknown_section_ignored(self):
        b = ContextBuilder.create().add("Mission", {"x": 1})
        b = b.add("Bogus", {"y": 2})
        snap = b.build()
        self.assertNotIn("Bogus", snap.sections)

    def test_builder_immutable(self):
        b = ContextBuilder.create()
        b2 = b.add("Mission", {"id": 1})
        self.assertNotIn("Mission", b.build().sections)  # asli tak berubah


class TestContextSummary(unittest.TestCase):
    def test_summary(self):
        sm = ContextSummary().summarize(build_full())
        self.assertEqual(sm["section_count"], len(SECTION_NAMES))
        self.assertEqual(sm["payload_size"]["Mission"], 1)


class TestContextValidator(unittest.TestCase):
    def test_complete(self):
        v = ContextValidator(required=SECTION_NAMES)
        self.assertTrue(v.is_complete(build_full()))

    def test_missing(self):
        v = ContextValidator(required=SECTION_NAMES)
        snap = ContextBuilder.create().build()  # kosong
        self.assertFalse(v.is_complete(snap))
        issues = v.validate(snap)
        self.assertTrue(any(i.code == "MISSING" for i in issues))

    def test_empty_section(self):
        v = ContextValidator(required=("Mission",))
        snap = ContextSnapshot(sections={"Mission": {}}, order=("Mission",))
        issues = v.validate(snap)
        self.assertTrue(any(i.code == "EMPTY" for i in issues))


class TestContextReport(unittest.TestCase):
    def test_report(self):
        r = ContextReport().build(build_full())
        self.assertEqual(r["summary"]["count"], len(SECTION_NAMES))
        self.assertIn("context", r)


if __name__ == "__main__":
    unittest.main()
