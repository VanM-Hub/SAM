"""Sprint 264 - Context Assembly: test lanjutan."""
import unittest

from sam.intelligence_runtime.context_builder import (
    ContextBuilder,
    DEFAULT_SECTIONS,
)
from sam.intelligence_runtime.context_report import ContextReport
from sam.intelligence_runtime.context_snapshot import ContextSnapshot
from sam.intelligence_runtime.context_summary import ContextSummary
from sam.intelligence_runtime.context_validator import (
    ContextIssue,
    ContextValidator,
)


SECTION_NAMES = DEFAULT_SECTIONS


def full_snapshot():
    b = ContextBuilder.create()
    for s in SECTION_NAMES:
        b = b.add(s, {"id": s.lower()})
    return b.build()


class TestContextSnapshotBehavior(unittest.TestCase):
    def test_empty_default(self):
        s = ContextSnapshot()
        self.assertEqual(s.sections, {})
        self.assertEqual(s.order, ())

    def test_section_missing_returns_empty(self):
        s = ContextSnapshot()
        self.assertEqual(s.section("Mission"), {})

    def test_as_dict_sections(self):
        s = ContextSnapshot(sections={"Mission": {"a": 1}}, order=("Mission",))
        d = s.as_dict()
        self.assertEqual(d["sections"]["Mission"], {"a": 1})


class TestContextBuilderBehavior(unittest.TestCase):
    def test_default_order(self):
        b = ContextBuilder.create()
        self.assertEqual(b._order, DEFAULT_SECTIONS)

    def test_add_overwrites(self):
        b = ContextBuilder.create().add("Mission", {"v": 1})
        b2 = b.add("Mission", {"v": 2})
        self.assertEqual(b2.build().sections["Mission"], {"v": 2})

    def test_ordering_by_default(self):
        b = ContextBuilder.create().add("Execution", {"x": 1})
        snap = b.build()
        # Execution hadir, tapi urutan tetap default
        self.assertIn("Execution", list(snap.sections.keys()))


class TestContextValidatorBehavior(unittest.TestCase):
    def test_issue_frozen(self):
        i = ContextIssue(section="Mission", code="X", message="m")
        with self.assertRaises(Exception):
            i.code = "Y"

    def test_multiple_missing(self):
        v = ContextValidator(required=("A", "B", "C"))
        issues = v.validate(ContextSnapshot())
        self.assertEqual(len(issues), 3)
        codes = [i.code for i in issues]
        self.assertEqual(codes, ["MISSING"] * 3)

    def test_required_empty(self):
        v = ContextValidator(required=())
        self.assertTrue(v.is_complete(ContextSnapshot()))

    def test_partial_present(self):
        v = ContextValidator(required=("A", "B", "C"))
        s = ContextSnapshot(sections={"A": {"x": 1}}, order=("A",))
        self.assertFalse(v.is_complete(s))
        names = [i.section for i in v.validate(s)]
        self.assertIn("B", names)


class TestContextSummaryBehavior(unittest.TestCase):
    def test_empty_summary(self):
        sm = ContextSummary().summarize(ContextSnapshot())
        self.assertEqual(sm["section_count"], 0)

    def test_payload_size(self):
        s = ContextSnapshot(
            sections={"Mission": {"a": 1, "b": 2}}, order=("Mission",))
        sm = ContextSummary().summarize(s)
        self.assertEqual(sm["payload_size"]["Mission"], 2)


class TestContextReportBehavior(unittest.TestCase):
    def test_report_json_shape(self):
        r = ContextReport().build(full_snapshot())
        self.assertIn("context", r)
        self.assertIn("summary", r)
        self.assertEqual(r["summary"]["count"], len(SECTION_NAMES))

    def test_report_immutable_input(self):
        snap = full_snapshot()
        _ = ContextReport().build(snap)
        self.assertEqual(len(snap.sections), len(SECTION_NAMES))  # tak berubah


if __name__ == "__main__":
    unittest.main()
