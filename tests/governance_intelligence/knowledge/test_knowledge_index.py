"""knowledge — WP-01..03 tests (IP-3.1-001)."""

import pytest
from pydantic import ValidationError

from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem
from sam.governance_intelligence.knowledge.indexes import index_mission
from sam.governance_intelligence.knowledge.loader import build_items, read_sections


class TestKnowledgeItem:
    def test_immutable(self):
        it = KnowledgeItem(
            key="mission.objective",
            kind="mission",
            source="m.md",
            title="Objective",
            content="x",
            signature="sig",
        )
        with pytest.raises(ValidationError):
            it.title = "mut"  # type: ignore[misc]

    def test_requires_key_source(self):
        with pytest.raises(ValidationError):
            KnowledgeItem(kind="mission", title="t", content="c", signature="s")  # type: ignore[call-arg]

    def test_carries_signature(self):
        it = KnowledgeItem(
            key="k", kind="g", source="s", title="t", content="hello", signature="abc"
        )
        assert it.signature == "abc"
        assert it.public_dict()["content"] == "hello"


class TestKnowledgeIndex:
    def test_by_key_finds_latest(self):
        idx = KnowledgeIndex(
            name="t",
            items=[
                KnowledgeItem(key="a", kind="g", source="s", title="t", content="1", signature="x"),
                KnowledgeItem(key="b", kind="g", source="s", title="t", content="2", signature="y"),
            ],
        )
        assert idx.by_key("a").content == "1"
        assert idx.by_key("zzz") is None
        assert idx.size() == 2

    def test_by_kind(self):
        idx = KnowledgeIndex(
            name="t",
            items=[
                KnowledgeItem(key="a", kind="mission", source="s", title="t", content="1", signature="x"),
                KnowledgeItem(key="b", kind="adr", source="s", title="t", content="2", signature="y"),
            ],
        )
        assert len(idx.by_kind("mission")) == 1


class TestLoader:
    def test_read_sections_top_down(self):
        secs = read_sections("# A\nbody\n# B\nmore")
        assert [s.heading for s in secs] == ["A", "B"]

    def test_build_items_traceability(self):
        items = build_items("m.md", "mission", "# Objective\n\nDo things.")
        assert len(items) == 1
        assert items[0].source == "m.md"
        assert items[0].kind == "mission"
        assert items[0].section == "Objective"


class TestMissionIndex:
    def test_facets_remap(self, mission_content):
        idx = index_mission("m.md", mission_content)
        assert idx.by_key("mission.objective") is not None
        assert idx.by_key("mission.scope") is not None
        assert idx.by_key("mission.lifecycle") is not None
