"""Tests for Collaboration Workflows & Task Delegation — Sprint 26 Fase 3.

Delegation lifecycle (REQUESTED→ACCEPTED→IN_PROGRESS→COMPLETED/FAILED,
REQUESTED→REJECTED, →TIMEOUT) and Collaboration Workflow execution.
"""

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio

from sam.persistence.database import Database
from sam.collaboration.delegation import (
    DelegationRequest,
    DelegationStatus,
    DelegationManager,
)
from sam.collaboration.workflow import (
    CollaborationWorkflow,
    CollaborationWorkflowManager,
)


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


@pytest_asyncio.fixture
async def dm(db):
    return DelegationManager(db)


@pytest_asyncio.fixture
async def wfm(db, dm):
    return CollaborationWorkflowManager(db, dm)


def make_delegation(
    id: str = "del-1",
    task_id: str = "task-1",
    sender: str = "agent-alpha",
    target: str = "agent-beta",
    capability: str = "health-check",
    status: DelegationStatus = DelegationStatus.REQUESTED,
) -> DelegationRequest:
    return DelegationRequest(
        id=id,
        task_id=task_id,
        sender_agent_id=sender,
        target_agent_id=target,
        capability=capability,
        payload={"action": "run_check"},
        status=status,
    )


# ═══════════════════════════════════════════════
# DelegationRequest model tests
# ═══════════════════════════════════════════════

class TestDelegationRequestModel:
    def test_create_minimal(self):
        dr = DelegationRequest(
            id="d-1",
            task_id="t-1",
            sender_agent_id="a",
            target_agent_id="b",
            capability="ping",
            payload={"cmd": "ping"},
        )
        assert dr.status == DelegationStatus.REQUESTED
        assert dr.timeout_seconds == 60
        assert dr.result is None
        assert dr.error is None

    def test_create_with_all_fields(self):
        now = datetime.now(timezone.utc)
        dr = DelegationRequest(
            id="d-full",
            task_id="t-full",
            sender_agent_id="alpha",
            target_agent_id="beta",
            capability="repair",
            payload={"target": "node-1"},
            status=DelegationStatus.IN_PROGRESS,
            timeout_seconds=120,
            created_at=now,
            updated_at=now,
            result={"fixed": True},
            error=None,
        )
        assert dr.status == DelegationStatus.IN_PROGRESS
        assert dr.timeout_seconds == 120
        assert dr.result == {"fixed": True}

    def test_delegation_status_enum_values(self):
        assert DelegationStatus.REQUESTED.value == "REQUESTED"
        assert DelegationStatus.ACCEPTED.value == "ACCEPTED"
        assert DelegationStatus.REJECTED.value == "REJECTED"
        assert DelegationStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert DelegationStatus.COMPLETED.value == "COMPLETED"
        assert DelegationStatus.FAILED.value == "FAILED"
        assert DelegationStatus.TIMEOUT.value == "TIMEOUT"

    def test_to_dict_and_from_dict_roundtrip(self):
        dr = DelegationRequest(
            id="d-rt",
            task_id="t-rt",
            sender_agent_id="alpha",
            target_agent_id="beta",
            capability="deploy",
            payload={"version": "2.0"},
            status=DelegationStatus.COMPLETED,
            timeout_seconds=300,
            result={"deploy_id": "dep-42"},
        )
        d = dr.to_dict()
        dr2 = DelegationRequest.from_dict(d)
        assert dr2.id == dr.id
        assert dr2.task_id == dr.task_id
        assert dr2.sender_agent_id == dr.sender_agent_id
        assert dr2.target_agent_id == dr.target_agent_id
        assert dr2.capability == dr.capability
        assert dr2.payload == dr.payload
        assert dr2.status == dr.status
        assert dr2.timeout_seconds == dr.timeout_seconds
        assert dr2.result == dr.result

    def test_from_dict_with_json_strings(self):
        d = {
            "id": "d-js",
            "task_id": "t-js",
            "sender_agent_id": "alpha",
            "target_agent_id": "beta",
            "capability": "scan",
            "payload": '{"port": 8080}',
            "status": "FAILED",
            "timeout_seconds": 60,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": "Connection refused",
        }
        dr = DelegationRequest.from_dict(d)
        assert dr.capability == "scan"
        assert dr.payload == {"port": 8080}
        assert dr.status == DelegationStatus.FAILED
        assert dr.error == "Connection refused"


# ═══════════════════════════════════════════════
# Delegation lifecycle tests
# ═══════════════════════════════════════════════

class TestDelegationRequestDelegation:
    @pytest.mark.asyncio
    async def test_request_delegation(self, dm, db):
        dr = make_delegation()
        del_id = await dm.request_delegation(dr)
        assert del_id == "del-1"
        row = await db.fetch_one(
            "SELECT * FROM delegation_requests WHERE id = ?", (del_id,)
        )
        assert row is not None
        assert row["status"] == "REQUESTED"

    @pytest.mark.asyncio
    async def test_get_delegation(self, dm):
        dr = make_delegation(id="del-get")
        await dm.request_delegation(dr)
        found = await dm.get_delegation("del-get")
        assert found is not None
        assert found.id == "del-get"

    @pytest.mark.asyncio
    async def test_get_delegation_nonexistent(self, dm):
        found = await dm.get_delegation("ghost-del")
        assert found is None


class TestDelegationAccept:
    @pytest.mark.asyncio
    async def test_accept(self, dm):
        dr = make_delegation(id="del-accept")
        await dm.request_delegation(dr)
        await dm.accept_delegation("del-accept")
        stored = await dm.get_delegation("del-accept")
        assert stored.status == DelegationStatus.ACCEPTED

    @pytest.mark.asyncio
    async def test_accept_invalid_transition(self, dm):
        dr = make_delegation(id="del-accept-inv", status=DelegationStatus.COMPLETED)
        await dm.request_delegation(dr)
        with pytest.raises(ValueError, match="Cannot transition"):
            await dm.accept_delegation("del-accept-inv")

    @pytest.mark.asyncio
    async def test_accept_nonexistent(self, dm):
        with pytest.raises(ValueError, match="Delegation not found"):
            await dm.accept_delegation("ghost-del")


class TestDelegationReject:
    @pytest.mark.asyncio
    async def test_reject(self, dm):
        dr = make_delegation(id="del-rej")
        await dm.request_delegation(dr)
        await dm.reject_delegation("del-rej", "not enough capacity")
        stored = await dm.get_delegation("del-rej")
        assert stored.status == DelegationStatus.REJECTED
        assert stored.error == "not enough capacity"

    @pytest.mark.asyncio
    async def test_reject_invalid_transition(self, dm):
        dr = make_delegation(id="del-rej-inv", status=DelegationStatus.COMPLETED)
        await dm.request_delegation(dr)
        with pytest.raises(ValueError, match="Cannot transition"):
            await dm.reject_delegation("del-rej-inv", "nope")


class TestDelegationStart:
    @pytest.mark.asyncio
    async def test_start(self, dm):
        dr = make_delegation(id="del-start")
        await dm.request_delegation(dr)
        await dm.accept_delegation("del-start")
        await dm.start_delegation("del-start")
        stored = await dm.get_delegation("del-start")
        assert stored.status == DelegationStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_start_from_requested_fails(self, dm):
        dr = make_delegation(id="del-start-inv")
        await dm.request_delegation(dr)
        with pytest.raises(ValueError, match="Cannot transition"):
            await dm.start_delegation("del-start-inv")


class TestDelegationComplete:
    @pytest.mark.asyncio
    async def test_complete(self, dm):
        dr = make_delegation(id="del-comp", status=DelegationStatus.IN_PROGRESS)
        await dm.request_delegation(dr)
        await dm.complete_delegation("del-comp", {"success": True, "data": "ok"})
        stored = await dm.get_delegation("del-comp")
        assert stored.status == DelegationStatus.COMPLETED
        assert stored.result == {"success": True, "data": "ok"}

    @pytest.mark.asyncio
    async def test_complete_invalid_transition(self, dm):
        dr = make_delegation(id="del-comp-inv", status=DelegationStatus.REQUESTED)
        await dm.request_delegation(dr)
        with pytest.raises(ValueError, match="Cannot transition"):
            await dm.complete_delegation("del-comp-inv", {"x": "y"})


class TestDelegationFail:
    @pytest.mark.asyncio
    async def test_fail(self, dm):
        dr = make_delegation(id="del-fail", status=DelegationStatus.IN_PROGRESS)
        await dm.request_delegation(dr)
        await dm.fail_delegation("del-fail", "unexpected error")
        stored = await dm.get_delegation("del-fail")
        assert stored.status == DelegationStatus.FAILED
        assert stored.error == "unexpected error"

    @pytest.mark.asyncio
    async def test_fail_invalid_transition(self, dm):
        dr = make_delegation(id="del-fail-inv", status=DelegationStatus.REQUESTED)
        await dm.request_delegation(dr)
        with pytest.raises(ValueError, match="Cannot transition"):
            await dm.fail_delegation("del-fail-inv", "err")


class TestDelegationTimeout:
    @pytest.mark.asyncio
    async def test_timeout(self, dm):
        dr = make_delegation(id="del-to")
        await dm.request_delegation(dr)
        await dm.timeout_delegation("del-to")
        stored = await dm.get_delegation("del-to")
        assert stored.status == DelegationStatus.TIMEOUT
        assert stored.error == "Delegation timed out"

    @pytest.mark.asyncio
    async def test_timeout_accepted(self, dm):
        dr = make_delegation(id="del-to-acc")
        await dm.request_delegation(dr)
        await dm.accept_delegation("del-to-acc")
        await dm.timeout_delegation("del-to-acc")
        stored = await dm.get_delegation("del-to-acc")
        assert stored.status == DelegationStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_timeout_completed_fails(self, dm):
        dr = make_delegation(id="del-to-inv", status=DelegationStatus.COMPLETED)
        await dm.request_delegation(dr)
        with pytest.raises(ValueError, match="Cannot transition"):
            await dm.timeout_delegation("del-to-inv")


class TestDelegationFullLifecycle:
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, dm):
        """REQUESTED → ACCEPTED → IN_PROGRESS → COMPLETED."""
        dr = make_delegation(id="del-fl")
        await dm.request_delegation(dr)
        assert (await dm.get_delegation("del-fl")).status == DelegationStatus.REQUESTED

        await dm.accept_delegation("del-fl")
        assert (await dm.get_delegation("del-fl")).status == DelegationStatus.ACCEPTED

        await dm.start_delegation("del-fl")
        assert (await dm.get_delegation("del-fl")).status == DelegationStatus.IN_PROGRESS

        await dm.complete_delegation("del-fl", {"done": True})
        assert (await dm.get_delegation("del-fl")).status == DelegationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_rejected_lifecycle(self, dm):
        """REQUESTED → REJECTED."""
        dr = make_delegation(id="del-rl")
        await dm.request_delegation(dr)
        await dm.reject_delegation("del-rl", "busy")
        assert (await dm.get_delegation("del-rl")).status == DelegationStatus.REJECTED

    @pytest.mark.asyncio
    async def test_failed_lifecycle(self, dm):
        """REQUESTED → ACCEPTED → IN_PROGRESS → FAILED."""
        dr = make_delegation(id="del-fail-lc")
        await dm.request_delegation(dr)
        await dm.accept_delegation("del-fail-lc")
        await dm.start_delegation("del-fail-lc")
        await dm.fail_delegation("del-fail-lc", "crash")
        assert (await dm.get_delegation("del-fail-lc")).status == DelegationStatus.FAILED


class TestDelegationQueries:
    @pytest.mark.asyncio
    async def test_get_pending_for_agent(self, dm):
        await dm.request_delegation(make_delegation(id="d-p1", target="agent-gamma"))
        await dm.request_delegation(make_delegation(id="d-p2", target="agent-gamma"))
        # One for a different agent
        await dm.request_delegation(make_delegation(id="d-p3", target="agent-other"))

        pending = await dm.get_pending_for_agent("agent-gamma")
        assert len(pending) == 2
        assert all(d.status == DelegationStatus.REQUESTED for d in pending)

    @pytest.mark.asyncio
    async def test_get_pending_for_agent_none(self, dm):
        pending = await dm.get_pending_for_agent("agent-ghost")
        assert pending == []

    @pytest.mark.asyncio
    async def test_get_active_for_agent(self, dm):
        d1 = make_delegation(id="d-a1", target="agent-gamma")
        await dm.request_delegation(d1)
        await dm.accept_delegation("d-a1")
        await dm.start_delegation("d-a1")  # now IN_PROGRESS

        d2 = make_delegation(id="d-a2", target="agent-gamma")
        await dm.request_delegation(d2)
        await dm.accept_delegation("d-a2")  # ACCEPTED

        active = await dm.get_active_for_agent("agent-gamma")
        assert len(active) == 2

    @pytest.mark.asyncio
    async def test_get_history_for_agent(self, dm):
        """Both as sender and target."""
        await dm.request_delegation(make_delegation(id="d-h1", sender="agent-a", target="agent-b"))
        await dm.request_delegation(make_delegation(id="d-h2", sender="agent-b", target="agent-a"))
        await dm.request_delegation(make_delegation(id="d-h3", sender="agent-c", target="agent-a"))

        history = await dm.get_history_for_agent("agent-a")
        assert len(history) >= 3

    @pytest.mark.asyncio
    async def test_get_history_limit(self, dm):
        for i in range(5):
            await dm.request_delegation(make_delegation(
                id=f"d-hl-{i}", sender="agent-a", target="agent-b"
            ))
        history = await dm.get_history_for_agent("agent-a", limit=3)
        assert len(history) == 3


# ═══════════════════════════════════════════════
# CollaborationWorkflow model tests
# ═══════════════════════════════════════════════

class TestCollaborationWorkflowModel:
    def test_create_minimal(self):
        wf = CollaborationWorkflow(
            id="wf-1",
            name="Health Check Pipeline",
            steps=[
                {"target_agent_id": "agent-alpha", "capability": "ping", "payload": {}},
            ],
        )
        assert wf.status == "PENDING"
        assert len(wf.steps) == 1

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid workflow status"):
            CollaborationWorkflow(
                id="wf-bad",
                name="Bad WF",
                steps=[],
                status="UNKNOWN",
            )

    def test_to_dict_and_from_dict_roundtrip(self):
        wf = CollaborationWorkflow(
            id="wf-rt",
            name="Deploy Pipeline",
            steps=[
                {"target_agent_id": "a1", "capability": "build", "payload": {"ver": "1.0"}},
                {"target_agent_id": "a2", "capability": "test", "payload": {}},
            ],
            status="RUNNING",
        )
        d = wf.to_dict()
        wf2 = CollaborationWorkflow.from_dict(d)
        assert wf2.id == wf.id
        assert wf2.name == wf.name
        assert len(wf2.steps) == 2
        assert wf2.status == "RUNNING"

    def test_from_dict_with_json_string_steps(self):
        d = {
            "id": "wf-js",
            "name": "JSON WF",
            "steps": '[{"target_agent_id": "a1", "capability": "x"}]',
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        wf = CollaborationWorkflow.from_dict(d)
        assert len(wf.steps) == 1
        assert wf.steps[0]["target_agent_id"] == "a1"


# ═══════════════════════════════════════════════
# CollaborationWorkflowManager tests
# ═══════════════════════════════════════════════

class TestWorkflowManagerCreate:
    @pytest.mark.asyncio
    async def test_create_workflow(self, wfm, db):
        wf = CollaborationWorkflow(
            id="wf-create",
            name="Test Pipeline",
            steps=[{"target_agent_id": "a1", "capability": "ping", "payload": {}}],
        )
        wf_id = await wfm.create_workflow(wf)
        assert wf_id == "wf-create"
        row = await db.fetch_one(
            "SELECT * FROM collaboration_workflows WHERE id = ?", (wf_id,)
        )
        assert row is not None
        assert row["name"] == "Test Pipeline"

    @pytest.mark.asyncio
    async def test_get_workflow(self, wfm):
        wf = CollaborationWorkflow(id="wf-get", name="Get Test", steps=[])
        await wfm.create_workflow(wf)
        found = await wfm.get_workflow("wf-get")
        assert found is not None
        assert found.name == "Get Test"

    @pytest.mark.asyncio
    async def test_get_workflow_nonexistent(self, wfm):
        found = await wfm.get_workflow("ghost-wf")
        assert found is None


class TestWorkflowManagerExecute:
    @pytest.mark.asyncio
    async def test_execute_workflow_creates_delegations(self, wfm):
        wf = CollaborationWorkflow(
            id="wf-exec",
            name="Exec Test",
            steps=[
                {"target_agent_id": "agent-alpha", "capability": "ping", "payload": {"cmd": "ping"}},
                {"target_agent_id": "agent-beta", "capability": "health", "payload": {"node": "n1"}},
            ],
        )
        await wfm.create_workflow(wf)
        wf_id = await wfm.execute_workflow("wf-exec")
        assert wf_id == "wf-exec"

        stored = await wfm.get_workflow("wf-exec")
        assert stored.status == "COMPLETED"
        assert len(stored.steps) == 2
        # Each step should have a delegation_id
        assert "delegation_id" in stored.steps[0]
        assert "delegation_id" in stored.steps[1]

    @pytest.mark.asyncio
    async def test_execute_nonexistent_raises(self, wfm):
        with pytest.raises(ValueError, match="Workflow not found"):
            await wfm.execute_workflow("ghost-wf")

    @pytest.mark.asyncio
    async def test_get_workflow_status(self, wfm):
        wf = CollaborationWorkflow(id="wf-status", name="Status Test", steps=[])
        await wfm.create_workflow(wf)
        status = await wfm.get_workflow_status("wf-status")
        assert status == "PENDING"

    @pytest.mark.asyncio
    async def test_get_workflow_status_nonexistent(self, wfm):
        with pytest.raises(ValueError, match="Workflow not found"):
            await wfm.get_workflow_status("ghost-wf")


class TestWorkflowManagerList:
    @pytest.mark.asyncio
    async def test_list_workflows(self, wfm):
        for i in range(3):
            await wfm.create_workflow(CollaborationWorkflow(
                id=f"wf-list-{i}", name=f"WF {i}", steps=[],
            ))
        wfs = await wfm.list_workflows()
        assert len(wfs) >= 3

    @pytest.mark.asyncio
    async def test_list_workflows_by_status(self, wfm):
        await wfm.create_workflow(CollaborationWorkflow(
            id="wf-pending", name="Pending WF", steps=[], status="PENDING",
        ))
        await wfm.create_workflow(CollaborationWorkflow(
            id="wf-running", name="Running WF", steps=[], status="RUNNING",
        ))
        running = await wfm.list_workflows(status="RUNNING")
        assert len(running) == 1
        assert running[0].id == "wf-running"

    @pytest.mark.asyncio
    async def test_list_workflows_invalid_status(self, wfm):
        with pytest.raises(ValueError, match="Invalid status filter"):
            await wfm.list_workflows(status="UNKNOWN")


class TestWorkflowManagerWorkflowStatus:
    @pytest.mark.asyncio
    async def test_workflow_running_status(self, wfm):
        wf = CollaborationWorkflow(
            id="wf-run-stat",
            name="Run Status",
            steps=[{"target_agent_id": "agent-alpha", "capability": "ping", "payload": {}}],
        )
        await wfm.create_workflow(wf)
        await wfm.execute_workflow("wf-run-stat")
        status = await wfm.get_workflow_status("wf-run-stat")
        assert status == "COMPLETED"
