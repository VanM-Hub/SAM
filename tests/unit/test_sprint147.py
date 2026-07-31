"""Sprint 147 — SQLite Provider Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.providers.sqlite.sqlite_provider import SQLiteProvider
from sam.providers.sqlite.query_builder import SQLiteQuery, SQLiteQueryBuilder
from sam.providers.sqlite.query_validator import SQLiteQueryValidator, SQLiteQueryValidation
from sam.providers.sqlite.query_preview import SQLitePreview, SQLiteQueryPreview
from sam.providers.sqlite.query_history import SQLiteHistory, SQLiteHistoryEntry
from sam.providers.sqlite.conversation_sqlite import ConversationSQLiteBridge
from sam.providers.sqlite.dashboard_sqlite import DashboardSQLiteBridge
from sam.providers.base.base_provider import ProviderError
from sam.providers.dashboard.dashboard_provider import ExecutionCard


class TestSQLiteProvider:
    def test_descriptor(self):
        p = SQLiteProvider()
        assert p.descriptor.provider_type == "sqlite"

    def test_prepare_query(self):
        p = SQLiteProvider()
        r = p.prepare_query("SELECT * FROM users", "users")
        assert r["preview"] is True
        assert r["connected"] is False
        assert r["external_calls"] == 0

    def test_prepare_empty_raises(self):
        with pytest.raises(ProviderError):
            SQLiteProvider().prepare_query("")

    def test_external_always_zero(self):
        p = SQLiteProvider()
        p.prepare_query("SELECT 1")
        assert p.external_calls == 0


class TestSQLiteQuery:
    def test_render(self):
        q = SQLiteQuery("q1", "SELECT * FROM users", limit=10)
        assert q.render() == "SELECT * FROM users LIMIT 10"

    def test_render_no_limit(self):
        q = SQLiteQuery("q1", "SELECT * FROM users")
        assert q.render() == "SELECT * FROM users"

    def test_immutable(self):
        q = SQLiteQuery("q1", "SELECT 1")
        with pytest.raises(FrozenInstanceError):
            q.sql = "DROP TABLE x"


class TestSQLiteQueryBuilder:
    def test_build(self):
        q = SQLiteQueryBuilder().build("q1", "SELECT * FROM t", table="t")
        assert q.table == "t"


class TestSQLiteQueryValidator:
    def test_valid(self):
        v = SQLiteQueryValidator().validate(SQLiteQuery("q1", "SELECT * FROM t"))
        assert v.valid is True

    def test_empty_sql(self):
        v = SQLiteQueryValidator().validate(SQLiteQuery("q1", ""))
        assert v.valid is False

    def test_blocked_drop(self):
        v = SQLiteQueryValidator().validate(SQLiteQuery("q1", "DROP TABLE t"))
        assert v.valid is False

    def test_blocked_delete(self):
        v = SQLiteQueryValidator().validate(SQLiteQuery("q1", "DELETE FROM t"))
        assert v.valid is False


class TestSQLiteQueryPreview:
    def test_preview(self):
        q = SQLiteQueryBuilder().build("q1", "SELECT * FROM t")
        p = SQLiteQueryPreview().preview(q)
        assert p.executed is False
        assert p.connected is False
        assert p.external_calls == 0


class TestSQLiteHistory:
    def test_record(self):
        h = SQLiteHistory()
        h.record(SQLiteHistoryEntry("q1", "SELECT 1", validated=True))
        assert h.count() == 1

    def test_no_execution(self):
        h = SQLiteHistory()
        h.record(SQLiteHistoryEntry("q1", "SELECT 1"))
        assert h.total_external_calls() == 0


class TestConversationSQLiteBridge:
    def test_describe(self):
        b = ConversationSQLiteBridge(SQLiteProvider())
        assert "sqlite" in b.describe()

    def test_contract(self):
        b = ConversationSQLiteBridge(SQLiteProvider())
        assert "sqlite" in b.contract()

    def test_supports(self):
        b = ConversationSQLiteBridge(SQLiteProvider())
        assert b.supports("prepare")
        assert b.supports("preview")


class TestDashboardSQLiteBridge:
    def test_card(self):
        b = DashboardSQLiteBridge(SQLiteProvider())
        card = b.card()
        assert isinstance(card, ExecutionCard)
        assert card.provider_id == "sqlite"
        assert card.verdict == "ready"


class TestSQLiteImmutability:
    DTO_CLASSES = [
        SQLiteQuery, SQLiteQueryValidation,
        SQLitePreview, SQLiteHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
