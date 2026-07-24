"""
Test Governance Engine – Sprint 21 Fase 3

Covers:
- Merge strategy (priority: ESCALATE > REJECT > REQUIRE_APPROVAL > WAIT > ALLOW_WITH_WARNING > ALLOW)
- Load rules from database
- Per-evaluator results in aggregate
- Gating graph execution (gate_graph_execution)
- Error handling (evaluator crash)
"""

import pytest
import json
import os
import tempfile
from typing import Optional

from src.sam.governance.engine import GovernanceEngine
from src.sam.governance.models import GovernanceDecision, GovernanceResult, GovernanceRule
from src.sam.governance.evaluator import Evaluator, BaseEvaluator


# ── Fake / Mock Helpers ────────────────────────────────────────────


class _Graph:
    def __init__(self, id: str = "g-1", name: str = "test"):
        self.id = id
        self.name = name
        self.metadata = {}


class _Context:
    def __init__(self):
        self.execution_id = "exec-1"


def _g(id: str = "g-1") -> _Graph:
    return _Graph(id=id)


def _c() -> _Context:
    return _Context()


# ── Simple evaluators for testing ──────────────────────────────────


class _StubEvaluator(BaseEvaluator):
    """Evaluator that returns a fixed decision."""

    def __init__(self, name: str, decision: GovernanceDecision, reason="", warnings=None, approvals=None, suggested_delay=None, metadata=None):
        super().__init__()
        self._my_name = name
        self._decision = decision
        self._reason = reason
        self._warnings = warnings or []
        self._approvals = approvals or []
        self._delay = suggested_delay
        self._meta = metadata or {}

    @property
    def name(self) -> str:
        return self._my_name

    async def _do_evaluate(self, graph, context) -> GovernanceResult:
        return GovernanceResult(
            decision=self._decision,
            reason=self._reason,
            warnings=self._warnings,
            required_approvals=self._approvals,
            suggested_delay=self._delay,
            metadata=self._meta,
        )


class _CrashingEvaluator(BaseEvaluator):
    """Evaluator that raises an exception."""

    @property
    def name(self) -> str:
        return "crashing"

    async def _do_evaluate(self, graph, context) -> GovernanceResult:
        raise RuntimeError("simulated crash")


# ── Fake DB with minimal SQL support for test_db operations ────────


class _TestDB:
    """Minimal DB shim for governance engine tests.
    Supports execute + fetch_all for governance_rules and governance_results tables.
    """

    def __init__(self):
        self._data: dict = {}
        self._executed_queries = []

    async def execute(self, query: str, params=None):
        self._executed_queries.append(("execute", query, params))
        # For INSERT INTO governance_rules or governance_results, store for fetch
        upper = query.upper().strip()
        if "INTO GOVERNANCE_RULES" in upper:
            if params:
                row = {
                    "id": params[0],
                    "name": params[1],
                    "evaluator_type": params[2],
                    "condition": params[3] if len(params) > 3 else "",
                    "decision_override": params[4] if len(params) > 4 else None,
                    "enabled": params[5] if len(params) > 5 else 1,
                    "metadata_json": params[6] if len(params) > 6 else "{}",
                    "created_at": params[7] if len(params) > 7 else "",
                    "updated_at": params[8] if len(params) > 8 else "",
                }
                self._data.setdefault("governance_rules", []).append(row)
        elif "INTO GOVERNANCE_RESULTS" in upper:
            pass  # just record

    async def fetch_all(self, query: str, params=None):
        self._executed_queries.append(("fetch_all", query, params))
        return self._data.get("governance_rules", [])


class _PauseResumeEngine:
    """Fake engine that records pause/resume calls."""

    def __init__(self):
        self.paused: dict = {}
        self.resumed: list = []

    async def pause(self, graph_id: str, reason: str = ""):
        self.paused[graph_id] = reason

    async def resume(self, graph_id: str):
        self.resumed.append(graph_id)


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def engine():
    """Return a fresh GovernanceEngine with no evaluators."""
    return GovernanceEngine()


@pytest.fixture
def db():
    return _TestDB()


# ── Merge Strategy Tests ──────────────────────────────────────────


class TestMergeStrategy:

    @pytest.mark.asyncio
    async def test_all_allowed_merges_to_allowed(self, engine):
        await engine.add_evaluator(_StubEvaluator("risk", GovernanceDecision.ALLOW))
        await engine.add_evaluator(_StubEvaluator("approval", GovernanceDecision.ALLOW))
        result = await engine.evaluate(_g(), _c())
        assert result.decision == GovernanceDecision.ALLOW
        assert not result.is_blocked()

    @pytest.mark.asyncio
    async def test_warning_wins_over_allow(self, engine):
        await engine.add_evaluator(_StubEvaluator("risk", GovernanceDecision.ALLOW))
        await engine.add_evaluator(_StubEvaluator(
            "resource", GovernanceDecision.ALLOW_WITH_WARNING,
            reason="low memory", warnings=["memory < 20%"],
        ))
        result = await engine.evaluate(_g(), _c())
        assert result.decision == GovernanceDecision.ALLOW_WITH_WARNING
        assert "low memory" in result.reason
        assert "memory < 20%" in result.warnings

    @pytest.mark.asyncio
    async def test_wait_wins_over_warning(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "resource", GovernanceDecision.ALLOW_WITH_WARNING,
            reason="disk warning",
        ))
        await engine.add_evaluator(_StubEvaluator(
            "maintenance", GovernanceDecision.WAIT,
            reason="maintenance window", suggested_delay=300,
        ))
        result = await engine.evaluate(_g(), _c())
        assert result.decision == GovernanceDecision.WAIT
        assert result.suggested_delay == 300

    @pytest.mark.asyncio
    async def test_require_approval_wins_over_wait(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "maintenance", GovernanceDecision.WAIT,
            reason="window active", suggested_delay=60,
        ))
        await engine.add_evaluator(_StubEvaluator(
            "approval", GovernanceDecision.REQUIRE_APPROVAL,
            reason="sensitive targets", approvals=["sec-team"],
        ))
        result = await engine.evaluate(_g(), _c())
        assert result.decision == GovernanceDecision.REQUIRE_APPROVAL
        assert "sec-team" in result.required_approvals

    @pytest.mark.asyncio
    async def test_reject_wins_over_approval(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "approval", GovernanceDecision.REQUIRE_APPROVAL,
            approvals=["admin"],
        ))
        await engine.add_evaluator(_StubEvaluator(
            "cluster", GovernanceDecision.REJECT,
            reason="load > 95%",
        ))
        result = await engine.evaluate(_g(), _c())
        assert result.decision == GovernanceDecision.REJECT
        assert result.is_blocked()

    @pytest.mark.asyncio
    async def test_escalate_wins_over_reject(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "risk", GovernanceDecision.REJECT, reason="too risky",
        ))
        await engine.add_evaluator(_StubEvaluator(
            "policy", GovernanceDecision.ESCALATE, reason="manual review needed",
        ))
        result = await engine.evaluate(_g(), _c())
        assert result.decision == GovernanceDecision.ESCALATE

    @pytest.mark.asyncio
    async def test_no_evaluators_allows(self, engine):
        result = await engine.evaluate(_g(), _c())
        assert result.decision == GovernanceDecision.ALLOW
        assert "No evaluators" in result.reason


# ── Per-evaluator Results ─────────────────────────────────────────


class TestPerEvaluatorResults:

    @pytest.mark.asyncio
    async def test_evaluator_results_present(self, engine):
        await engine.add_evaluator(_StubEvaluator("risk", GovernanceDecision.ALLOW))
        await engine.add_evaluator(_StubEvaluator(
            "cluster", GovernanceDecision.ALLOW_WITH_WARNING,
            reason="moderate load",
        ))
        result = await engine.evaluate(_g(), _c())
        assert "risk" in result.evaluator_results
        assert "cluster" in result.evaluator_results
        assert result.evaluator_results["risk"].decision == GovernanceDecision.ALLOW
        assert result.evaluator_results["cluster"].decision == GovernanceDecision.ALLOW_WITH_WARNING

    @pytest.mark.asyncio
    async def test_reasons_merged(self, engine):
        await engine.add_evaluator(_StubEvaluator("risk", GovernanceDecision.ALLOW, reason="ok"))
        await engine.add_evaluator(_StubEvaluator("cluster", GovernanceDecision.ALLOW, reason="fine"))
        result = await engine.evaluate(_g(), _c())
        assert "[risk] ok" in result.reason
        assert "[cluster] fine" in result.reason

    @pytest.mark.asyncio
    async def test_approvals_deduplicated(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "a1", GovernanceDecision.REQUIRE_APPROVAL,
            approvals=["admin", "sec"],
        ))
        await engine.add_evaluator(_StubEvaluator(
            "a2", GovernanceDecision.REQUIRE_APPROVAL,
            approvals=["sec", "ops"],
        ))
        result = await engine.evaluate(_g(), _c())
        assert sorted(result.required_approvals) == ["admin", "ops", "sec"]

    @pytest.mark.asyncio
    async def test_metadata_collected(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "risk", GovernanceDecision.ALLOW, metadata={"score": 0.2},
        ))
        await engine.add_evaluator(_StubEvaluator(
            "cluster", GovernanceDecision.ALLOW, metadata={"load": 30.0},
        ))
        result = await engine.evaluate(_g(), _c())
        meta = result.metadata
        assert meta["risk"]["score"] == 0.2
        assert meta["cluster"]["load"] == 30.0
        assert meta["graph_id"] == "g-1"
        assert "risk" in meta["evaluators_run"]

    @pytest.mark.asyncio
    async def test_delay_takes_max(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "m1", GovernanceDecision.WAIT, suggested_delay=120,
        ))
        await engine.add_evaluator(_StubEvaluator(
            "m2", GovernanceDecision.WAIT, suggested_delay=300,
        ))
        result = await engine.evaluate(_g(), _c())
        assert result.suggested_delay == 300


# ── Error Handling ────────────────────────────────────────────────


class TestErrorHandling:

    @pytest.mark.asyncio
    async def test_evaluator_crash_treated_as_reject(self, engine):
        await engine.add_evaluator(_StubEvaluator("risk", GovernanceDecision.ALLOW))
        await engine.add_evaluator(_CrashingEvaluator())
        await engine.add_evaluator(_StubEvaluator("cluster", GovernanceDecision.ALLOW))
        result = await engine.evaluate(_g(), _c())
        # Crashing evaluator → REJECT, which dominates ALLOW
        assert result.decision == GovernanceDecision.REJECT
        assert "crashing" in result.evaluator_results
        assert "crashing" in result.reason

    @pytest.mark.asyncio
    async def test_all_evaluators_crash(self, engine):
        await engine.add_evaluator(_CrashingEvaluator())
        result = await engine.evaluate(_g(), _c())
        assert result.decision == GovernanceDecision.REJECT


# ── Load Rules from Database ──────────────────────────────────────


class TestLoadRules:

    @pytest.mark.asyncio
    async def test_load_rules_no_db(self, engine):
        rules = await engine.load_rules()
        assert rules == []

    @pytest.mark.asyncio
    async def test_load_rules_from_db(self, db):
        eng = GovernanceEngine(db=db)
        # Insert a rule via execute
        await db.execute(
            """INSERT INTO governance_rules (id, name, evaluator_type, condition, decision_override, enabled, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ["r1", "Test Rule", "POLICY", "flag=true", "REQUIRE_APPROVAL", 1, '{}', "2026-01-01T00:00:00", "2026-01-01T00:00:00"],
        )
        rules = await eng.load_rules()
        assert len(rules) == 1
        r = rules[0]
        assert r.id == "r1"
        assert r.name == "Test Rule"
        assert r.evaluator_type == "POLICY"
        assert r.condition == "flag=true"
        assert r.decision_override == GovernanceDecision.REQUIRE_APPROVAL
        assert r.enabled is True

    @pytest.mark.asyncio
    async def test_load_rules_empty_table(self, db):
        eng = GovernanceEngine(db=db)
        rules = await eng.load_rules()
        assert rules == []


# ── Gate Graph Execution ──────────────────────────────────────────


class TestGateGraphExecution:

    @pytest.mark.asyncio
    async def test_gate_allowed_returns_none(self, engine):
        await engine.add_evaluator(_StubEvaluator("risk", GovernanceDecision.ALLOW))
        fake_engine = _PauseResumeEngine()
        result = await engine.gate_graph_execution(_g(), _c(), fake_engine)
        assert result is None

    @pytest.mark.asyncio
    async def test_gate_warning_returns_none(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "resource", GovernanceDecision.ALLOW_WITH_WARNING, reason="warning",
        ))
        fake_engine = _PauseResumeEngine()
        result = await engine.gate_graph_execution(_g(), _c(), fake_engine)
        assert result is None

    @pytest.mark.asyncio
    async def test_gate_wait_pauses_and_returns_result(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "maintenance", GovernanceDecision.WAIT,
            reason="maintenance active", suggested_delay=30,
        ))
        fake_engine = _PauseResumeEngine()
        result = await engine.gate_graph_execution(_g(), _c(), fake_engine)
        assert result is not None
        assert result.decision == GovernanceDecision.WAIT
        assert "g-1" in fake_engine.paused
        assert "maintenance active" in fake_engine.paused["g-1"]

    @pytest.mark.asyncio
    async def test_gate_require_approval_pauses_and_returns_result(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "approval", GovernanceDecision.REQUIRE_APPROVAL,
            reason="needs approval", approvals=["ops"],
        ))
        fake_engine = _PauseResumeEngine()
        result = await engine.gate_graph_execution(_g(), _c(), fake_engine)
        assert result is not None
        assert result.decision == GovernanceDecision.REQUIRE_APPROVAL
        assert "g-1" in fake_engine.paused

    @pytest.mark.asyncio
    async def test_gate_reject_returns_result(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "cluster", GovernanceDecision.REJECT, reason="overloaded",
        ))
        fake_engine = _PauseResumeEngine()
        result = await engine.gate_graph_execution(_g(), _c(), fake_engine)
        assert result is not None
        assert result.decision == GovernanceDecision.REJECT

    @pytest.mark.asyncio
    async def test_gate_escalate_returns_result(self, engine):
        await engine.add_evaluator(_StubEvaluator(
            "policy", GovernanceDecision.ESCALATE, reason="needs review",
        ))
        fake_engine = _PauseResumeEngine()
        result = await engine.gate_graph_execution(_g(), _c(), fake_engine)
        assert result is not None
        assert result.decision == GovernanceDecision.ESCALATE


# ── Engine Lifecycle ──────────────────────────────────────────────


class TestEngineLifecycle:

    @pytest.mark.asyncio
    async def test_add_evaluator_increases_count(self, engine):
        assert engine.get_evaluators() == []
        await engine.add_evaluator(_StubEvaluator("risk", GovernanceDecision.ALLOW))
        assert len(engine.get_evaluators()) == 1

    @pytest.mark.asyncio
    async def test_get_rules_returns_loaded_rules(self, db):
        eng = GovernanceEngine(db=db)
        await db.execute(
            """INSERT INTO governance_rules (id, name, evaluator_type, condition, decision_override, enabled, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ["r1", "Rule 1", "POLICY", "test", None, 1, "{}", "", ""],
        )
        await eng.load_rules()
        rules = eng.get_rules()
        assert len(rules) == 1
        assert rules[0].id == "r1"

    @pytest.mark.asyncio
    async def test_reload_rules_refreshes(self, db):
        eng = GovernanceEngine(db=db)
        await db.execute(
            """INSERT INTO governance_rules (id, name, evaluator_type, condition, decision_override, enabled, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ["r1", "Rule 1", "POLICY", "", None, 1, "{}", "", ""],
        )
        rules1 = await eng.load_rules()
        assert len(rules1) == 1

        await db.execute(
            """INSERT INTO governance_rules (id, name, evaluator_type, condition, decision_override, enabled, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ["r2", "Rule 2", "RISK", "score>0.5", "REQUIRE_APPROVAL", 1, "{}", "", ""],
        )
        rules2 = await eng.load_rules()
        assert len(rules2) == 2

    @pytest.mark.asyncio
    async def test_store_result_without_db_no_error(self, engine):
        """Calling evaluate without a DB should not crash (store is skipped)."""
        await engine.add_evaluator(_StubEvaluator("risk", GovernanceDecision.ALLOW))
        result = await engine.evaluate(_g(), _c())
        assert result.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_load_rules_with_real_sqlite(self):
        """Integration test: load rules from a real SQLite database."""
        import sqlite3
        import asyncio

        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            # Create test DB with governance_rules table
            conn = sqlite3.connect(tmp_path)
            conn.row_factory = sqlite3.Row
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS governance_rules (
                    id TEXT PRIMARY KEY, name TEXT, evaluator_type TEXT,
                    condition TEXT DEFAULT '', decision_override TEXT,
                    enabled INTEGER DEFAULT 1, metadata_json TEXT DEFAULT '{}',
                    created_at TEXT, updated_at TEXT
                );
                INSERT INTO governance_rules (id, name, evaluator_type, condition, decision_override, enabled, metadata_json, created_at, updated_at)
                VALUES ('r-int', 'Integration Rule', 'POLICY', 'env=prod', 'REJECT', 1, '{}', '2026-01-01', '2026-01-01');
            """)
            conn.commit()
            conn.close()

            # Create a real Database instance
            from src.sam.persistence.database import Database
            real_db = Database(tmp_path)

            eng = GovernanceEngine(db=real_db)
            rules = await eng.load_rules()
            assert len(rules) == 1
            assert rules[0].id == "r-int"
            assert rules[0].decision_override == GovernanceDecision.REJECT

            await real_db.close()
        finally:
            os.unlink(tmp_path)
