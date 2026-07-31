"""Sprint 208 — Policy Catalog Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.policy_runtime.catalog.policy_catalog import (
    PolicyCatalog, PolicyCatalogEntry,
)
from sam.policy_runtime.catalog.policy_index import PolicyIndex, PolicyIndexer
from sam.policy_runtime.catalog.policy_loader import (
    PolicyLoader, PolicyLoadResult,
)
from sam.policy_runtime.catalog.policy_version import (
    PolicyVersionInfo, PolicyVersionProvider,
)
from sam.policy_runtime.catalog.policy_history import (
    PolicyHistory, PolicyHistoryEntry,
)
from sam.policy_runtime.catalog.conversation_catalog import ConversationCatalogBridge
from sam.policy_runtime.catalog.dashboard_catalog import DashboardCatalogBridge
from sam.policy_runtime.model.policy import Policy
from sam.policy_runtime.model.policy_rule import PolicyRule
from sam.policy_runtime.dashboard import PolicyCard


def _pol():
    return Policy("pol1", rules=["r1", "r2"])


class TestPolicyCatalog:
    def test_add_get(self):
        c = PolicyCatalog()
        c.add(_pol())
        assert c.get("pol1").policy_id == "pol1"

    def test_count(self):
        c = PolicyCatalog()
        c.add(_pol())
        assert c.count() == 1

    def test_all_entries(self):
        c = PolicyCatalog()
        c.add(_pol())
        entries = c.all_entries()
        assert len(entries) == 1
        assert entries[0].rule_count == 2

    def test_by_scope(self):
        c = PolicyCatalog()
        c.add(_pol())
        c.add(Policy("pol2", scope="mission"))
        assert len(c.by_scope("system")) == 1

    def test_missing_get(self):
        assert PolicyCatalog().get("nope") is None

    def test_no_file_load(self):
        assert PolicyCatalog().count() == 0


class TestPolicyCatalogEntry:
    def test_immutable(self):
        e = PolicyCatalogEntry("pol")
        with pytest.raises(FrozenInstanceError):
            e.rule_count = 1


class TestPolicyIndexer:
    def test_index(self):
        pol = _pol()
        rules = [PolicyRule("r1", "pol1"), PolicyRule("r2", "pol1")]
        idx = PolicyIndexer().index(pol, rules)
        assert idx.rule_count == 2
        assert idx.has_rule("r1") is True

    def test_search(self):
        pol = _pol()
        rules = [PolicyRule("r1", "pol1"), PolicyRule("r2", "pol1")]
        idx = PolicyIndexer().index(pol, rules)
        results = PolicyIndexer().search(idx, "r")
        assert len(results) == 2


class TestPolicyIndex:
    def test_default(self):
        assert PolicyIndex().rule_count == 0

    def test_immutable(self):
        idx = PolicyIndex()
        with pytest.raises(FrozenInstanceError):
            idx.rule_count = 1


class TestPolicyLoader:
    def test_load_found(self):
        c = PolicyCatalog()
        c.add(_pol())
        r = PolicyLoader(c).load("pol1")
        assert r.ok is True
        assert r.policy.policy_id == "pol1"

    def test_load_missing(self):
        r = PolicyLoader(PolicyCatalog()).load("nope")
        assert r.ok is False
        assert r.detail == "not found"


class TestPolicyLoadResult:
    def test_default(self):
        assert PolicyLoadResult().ok is False

    def test_immutable(self):
        r = PolicyLoadResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = True


class TestPolicyVersionProvider:
    def test_provide(self):
        v = PolicyVersionProvider().provide("pol1")
        assert v.version == "21.0.0"
        assert v.policy_id == "pol1"


class TestPolicyVersionInfo:
    def test_immutable(self):
        v = PolicyVersionInfo()
        with pytest.raises(FrozenInstanceError):
            v.version = "x"


class TestPolicyHistory:
    def test_record_and_count(self):
        h = PolicyHistory()
        h.record(PolicyHistoryEntry("pol1", "created"))
        assert h.count() == 1

    def test_by_policy(self):
        h = PolicyHistory()
        h.record(PolicyHistoryEntry("pol1"))
        h.record(PolicyHistoryEntry("pol2"))
        assert len(h.by_policy("pol1")) == 1

    def test_default_action(self):
        e = PolicyHistoryEntry("pol1")
        assert e.action == "created"


class TestConversationCatalogBridge:
    def test_5_queries(self):
        b = ConversationCatalogBridge()
        pol = _pol()
        assert b.query_1_add(pol)["added"] == "pol1"
        assert b.query_2_load("pol1")["ok"] is True
        assert b.query_3_search("pol1", "r") == []
        assert b.query_4_version("pol1")["version"] == "21.0.0"
        assert b.query_5_history("pol1") == ["pol1"]

    def test_search_missing(self):
        assert ConversationCatalogBridge().query_3_search("nope", "x") == []


class TestDashboardCatalogBridge:
    def test_five_cards(self):
        b = DashboardCatalogBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_overview(self):
        b = DashboardCatalogBridge()
        assert b.overview_card().group == "catalog"


class TestCatalogImmutability:
    DTO_CLASSES = [
        PolicyCatalogEntry, PolicyIndex, PolicyLoadResult,
        PolicyVersionInfo, PolicyHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
