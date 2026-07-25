"""Tests for Template Evolution — Sprint 25 Fase 2.

TemplateEvolution model, TemplateEvolutionManager (evaluate, propose,
approve, apply, rollback, reject, history).
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio

from sam.persistence.database import Database
from sam.institutional.evolution import (
    TemplateEvolution,
    TemplateEvolutionManager,
    EVOLUTION_STATUSES,
    MIN_EVALUATION_EXECUTIONS,
)
from sam.institutional.memory import InstitutionalMemory, InstitutionalMemoryManager


@pytest_asyncio.fixture
async def db():
    """Create temporary database with all migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    database = Database(db_path)
    await database.initialize()
    from sam.persistence.migrations.manager import MigrationManager
    migrations_dir = Path(__file__).parent.parent / "sam" / "persistence" / "migrations"
    manager = MigrationManager(database, str(migrations_dir))
    await manager.migrate()
    yield database
    await database.close()
    Path(db_path).unlink(missing_ok=True)


# ─────────────────────────────────────────────
# TemplateEvolution model tests
# ─────────────────────────────────────────────

class TestTemplateEvolutionModel:
    def test_create_minimal(self):
        evo = TemplateEvolution(
            id="evo-1",
            template_id="tmpl-1",
            original_version="1.0",
            new_version="2.0",
        )
        assert evo.id == "evo-1"
        assert evo.template_id == "tmpl-1"
        assert evo.original_version == "1.0"
        assert evo.new_version == "2.0"
        assert evo.status == "PROPOSED"
        assert evo.changes == []
        assert evo.evidence == []
        assert evo.applied_at is None

    def test_create_with_all_fields(self):
        now = datetime.now(timezone.utc)
        evo = TemplateEvolution(
            id="evo-full",
            template_id="tmpl-42",
            original_version="v1",
            new_version="v2",
            changes=[{"action": "add_node", "node_id": "n3"}],
            reason="Performance improvement",
            evidence=["ev-1", "ev-2"],
            status="APPLIED",
            proposed_at=now,
            applied_at=now,
            created_at=now,
            updated_at=now,
        )
        assert evo.status == "APPLIED"
        assert len(evo.changes) == 1
        assert len(evo.evidence) == 2
        assert evo.applied_at is not None

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            TemplateEvolution(
                id="evo-bad",
                template_id="tmpl",
                original_version="1",
                new_version="2",
                status="INVALID",
            )

    def test_all_statuses_accepted(self):
        for s in EVOLUTION_STATUSES:
            evo = TemplateEvolution(
                id=f"evo-{s}",
                template_id="tmpl",
                original_version="1",
                new_version="2",
                status=s,
            )
            assert evo.status == s

    def test_to_dict_and_from_dict_roundtrip(self):
        now = datetime.now(timezone.utc)
        evo = TemplateEvolution(
            id="evo-rt",
            template_id="tmpl-test",
            original_version="1.0",
            new_version="1.5",
            changes=[{"action": "modify_node", "node_id": "n1", "diff": "retry_policy changed"}],
            reason="Better retry handling",
            evidence=["inst-mem-1", "inst-mem-2"],
            status="APPROVED",
            proposed_at=now,
            created_at=now,
            updated_at=now,
        )
        d = evo.to_dict()
        evo2 = TemplateEvolution.from_dict(d)
        assert evo2.id == evo.id
        assert evo2.template_id == evo.template_id
        assert evo2.original_version == evo.original_version
        assert evo2.new_version == evo.new_version
        assert evo2.changes == evo.changes
        assert evo2.reason == evo.reason
        assert evo2.evidence == evo.evidence
        assert evo2.status == evo.status
        assert evo2.proposed_at is not None

    def test_from_dict_with_json_strings(self):
        d = {
            "id": "evo-js",
            "template_id": "tmpl",
            "original_version": "1",
            "new_version": "2",
            "changes": '[{"action":"add_node"}]',
            "evidence": '["ev-1"]',
            "status": "PROPOSED",
            "proposed_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        evo = TemplateEvolution.from_dict(d)
        assert evo.changes == [{"action": "add_node"}]
        assert evo.evidence == ["ev-1"]


# ─────────────────────────────────────────────
# TemplateEvolutionManager tests
# ─────────────────────────────────────────────

class TestTemplateEvolutionManagerEvaluation:
    @pytest.mark.asyncio
    async def test_evaluate_no_memory_returns_insufficient(self, db):
        """Without memory_manager, evaluation returns has_sufficient_data=False."""
        manager = TemplateEvolutionManager(db, memory_manager=None)
        result = await manager.evaluate_template("tmpl-nobody")
        assert result["has_sufficient_data"] is False
        assert result["recommendation"] == "insufficient_data"
        assert result["total_executions"] == 0

    @pytest.mark.asyncio
    async def test_evaluate_insufficient_data(self, db):
        """Less than MIN_EVALUATION_EXECUTIONS returns insufficient."""
        mem_mgr = InstitutionalMemoryManager(db)
        manager = TemplateEvolutionManager(db, memory_manager=mem_mgr)
        # Store only 1 memory (need MIN=3)
        await mem_mgr.store(InstitutionalMemory(
            id="eval-m1", type="KNOWLEDGE", content={},
            source="tmpl-test", success_count=1, failure_count=0,
        ))
        result = await manager.evaluate_template("tmpl-test")
        assert result["total_executions"] == 1
        assert result["has_sufficient_data"] is False

    @pytest.mark.asyncio
    async def test_evaluate_sufficient_data_stable(self, db):
        mem_mgr = InstitutionalMemoryManager(db)
        manager = TemplateEvolutionManager(db, memory_manager=mem_mgr)
        for i in range(MIN_EVALUATION_EXECUTIONS):
            await mem_mgr.store(InstitutionalMemory(
                id=f"eval-stable-{i}", type="KNOWLEDGE", content={},
                source="tmpl-stable", success_count=5, failure_count=1,
                confidence=0.9,
            ))
        result = await manager.evaluate_template("tmpl-stable")
        assert result["has_sufficient_data"] is True
        assert result["total_executions"] >= MIN_EVALUATION_EXECUTIONS
        assert result["recommendation"] == "stable"

    @pytest.mark.asyncio
    async def test_evaluate_needs_improvement(self, db):
        mem_mgr = InstitutionalMemoryManager(db)
        manager = TemplateEvolutionManager(db, memory_manager=mem_mgr)
        for i in range(MIN_EVALUATION_EXECUTIONS):
            await mem_mgr.store(InstitutionalMemory(
                id=f"eval-bad-{i}", type="KNOWLEDGE", content={},
                source="tmpl-bad", success_count=1, failure_count=5,
                confidence=0.3,
            ))
        result = await manager.evaluate_template("tmpl-bad")
        assert result["has_sufficient_data"] is True
        assert result["recommendation"] == "needs_improvement"
        assert result["success_rate"] < 0.5

    @pytest.mark.asyncio
    async def test_evaluate_partial_no_data_unchanged(self, db):
        """Template with no institutional memory entries at all."""
        mem_mgr = InstitutionalMemoryManager(db)
        manager = TemplateEvolutionManager(db, memory_manager=mem_mgr)
        result = await manager.evaluate_template("tmpl-ghost")
        assert result["has_sufficient_data"] is False
        assert result["total_executions"] == 0


class TestTemplateEvolutionManagerPropose:
    @pytest.mark.asyncio
    async def test_propose_evolution_creates_record(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution(
            template_id="tmpl-propose",
            changes=[{"action": "add_node", "node_id": "n4"}],
            reason="Need caching step",
        )
        assert evo.status == "PROPOSED"
        assert evo.template_id == "tmpl-propose"
        assert evo.id is not None

        # Verify persisted
        row = await db.fetch_one(
            "SELECT * FROM template_evolutions WHERE id = ?", (evo.id,)
        )
        assert row is not None
        assert row["status"] == "PROPOSED"

    @pytest.mark.asyncio
    async def test_propose_multiple_evolutions(self, db):
        manager = TemplateEvolutionManager(db)
        evo1 = await manager.propose_evolution("tmpl-multi", [], "first")
        evo2 = await manager.propose_evolution("tmpl-multi", [], "second")
        assert evo1.id != evo2.id
        history = await manager.get_evolution_history("tmpl-multi")
        assert len(history) == 2


class TestTemplateEvolutionManagerApproval:
    @pytest.mark.asyncio
    async def test_approve_proposed(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution("tmpl-approve", [], "test")
        await manager.approve_evolution(evo.id)
        row = await db.fetch_one(
            "SELECT status FROM template_evolutions WHERE id = ?", (evo.id,)
        )
        assert row["status"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_approve_non_proposed_raises(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution("tmpl-bad-approve", [], "test")
        await manager.approve_evolution(evo.id)  # now APPROVED
        with pytest.raises(ValueError, match="Cannot approve"):
            await manager.approve_evolution(evo.id)

    @pytest.mark.asyncio
    async def test_approve_nonexistent_raises(self, db):
        manager = TemplateEvolutionManager(db)
        with pytest.raises(ValueError, match="Evolution not found"):
            await manager.approve_evolution("nonexistent-evo")


class TestTemplateEvolutionManagerApply:
    @pytest.mark.asyncio
    async def test_apply_approved(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution("tmpl-apply", [], "test")
        await manager.approve_evolution(evo.id)
        await manager.apply_evolution(evo.id)
        row = await db.fetch_one(
            "SELECT status, applied_at FROM template_evolutions WHERE id = ?",
            (evo.id,),
        )
        assert row["status"] == "APPLIED"
        assert row["applied_at"] is not None

    @pytest.mark.asyncio
    async def test_apply_non_approved_raises(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution("tmpl-bad-apply", [], "test")
        with pytest.raises(ValueError, match="Cannot apply"):
            await manager.apply_evolution(evo.id)

    @pytest.mark.asyncio
    async def test_apply_nonexistent_raises(self, db):
        manager = TemplateEvolutionManager(db)
        with pytest.raises(ValueError, match="Evolution not found"):
            await manager.apply_evolution("ghost-evo")


class TestTemplateEvolutionManagerRollback:
    @pytest.mark.asyncio
    async def test_rollback_applied(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution("tmpl-rollback", [], "test")
        await manager.approve_evolution(evo.id)
        await manager.apply_evolution(evo.id)
        await manager.rollback_evolution(evo.id)
        row = await db.fetch_one(
            "SELECT status FROM template_evolutions WHERE id = ?", (evo.id,)
        )
        assert row["status"] == "ROLLED_BACK"

    @pytest.mark.asyncio
    async def test_rollback_non_applied_raises(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution("tmpl-bad-rb", [], "test")
        with pytest.raises(ValueError, match="Cannot rollback"):
            await manager.rollback_evolution(evo.id)

    @pytest.mark.asyncio
    async def test_rollback_nonexistent_raises(self, db):
        manager = TemplateEvolutionManager(db)
        with pytest.raises(ValueError, match="Evolution not found"):
            await manager.rollback_evolution("ghost-rb")


class TestTemplateEvolutionManagerReject:
    @pytest.mark.asyncio
    async def test_reject_proposed(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution("tmpl-reject", [], "test")
        await manager.reject_evolution(evo.id)
        row = await db.fetch_one(
            "SELECT status FROM template_evolutions WHERE id = ?", (evo.id,)
        )
        assert row["status"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_reject_non_proposed_raises(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution("tmpl-bad-rej", [], "test")
        await manager.approve_evolution(evo.id)
        with pytest.raises(ValueError, match="Cannot reject"):
            await manager.reject_evolution(evo.id)


class TestTemplateEvolutionManagerHistory:
    @pytest.mark.asyncio
    async def test_get_evolution_history(self, db):
        manager = TemplateEvolutionManager(db)
        await manager.propose_evolution(
            "tmpl-hist", [{"action": "change_a"}], "first"
        )
        await manager.propose_evolution(
            "tmpl-hist", [{"action": "change_b"}], "second"
        )
        history = await manager.get_evolution_history("tmpl-hist")
        assert len(history) == 2
        # Newest first
        assert history[0].reason == "second"
        assert history[1].reason == "first"

    @pytest.mark.asyncio
    async def test_get_evolution_history_empty(self, db):
        manager = TemplateEvolutionManager(db)
        history = await manager.get_evolution_history("tmpl-no-history")
        assert history == []

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, db):
        """Test complete lifecycle: PROPOSED → APPROVED → APPLIED → ROLLED_BACK."""
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution(
            "tmpl-lifecycle",
            [{"action": "add_verify_node"}],
            "Add post-execution verification",
        )
        assert evo.status == "PROPOSED"

        await manager.approve_evolution(evo.id)
        assert (await manager._get_or_raise(evo.id)).status == "APPROVED"

        await manager.apply_evolution(evo.id)
        assert (await manager._get_or_raise(evo.id)).status == "APPLIED"

        await manager.rollback_evolution(evo.id)
        assert (await manager._get_or_raise(evo.id)).status == "ROLLED_BACK"

    @pytest.mark.asyncio
    async def test_propose_with_evidence(self, db):
        manager = TemplateEvolutionManager(db)
        evo = await manager.propose_evolution(
            "tmpl-evidence",
            [{"action": "modify_deps"}],
            "Fix dependency order",
        )
        # We can also manually attach evidence later via DB update
        # Verify the record exists and basic fields are correct
        stored = await manager._get_or_raise(evo.id)
        assert stored.reason == "Fix dependency order"
        assert stored.status == "PROPOSED"
