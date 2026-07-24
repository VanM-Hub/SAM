"""Tests for Agent Registry — Sprint 26 Fase 1.

Agent model + AgentRegistry (register, unregister, get, list,
heartbeat, find_by_capability, update_status).
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio

from sam.persistence.database import Database
from sam.collaboration.agent import Agent, AGENT_STATUSES
from sam.collaboration.registry import AgentRegistry


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
async def registry(db):
    return AgentRegistry(db)


# ─────────────────────────────────────────────
# Agent model tests
# ─────────────────────────────────────────────

class TestAgentModel:
    def test_create_minimal(self):
        agent = Agent(
            id="agent-1",
            name="Worker-A",
            endpoint="http://localhost:8080",
        )
        assert agent.id == "agent-1"
        assert agent.name == "Worker-A"
        assert agent.endpoint == "http://localhost:8080"
        assert agent.status == "ONLINE"
        assert agent.capabilities == []
        assert agent.metadata == {}
        assert agent.last_heartbeat is not None

    def test_create_with_all_fields(self):
        now = datetime.now(timezone.utc)
        agent = Agent(
            id="agent-full",
            name="Fully Loaded",
            endpoint="https://agent-01.sam.internal:9000",
            capabilities=["health-check", "repair", "deploy"],
            status="BUSY",
            metadata={"version": "2.0", "region": "us-east"},
            last_heartbeat=now,
            created_at=now,
        )
        assert agent.status == "BUSY"
        assert len(agent.capabilities) == 3
        assert agent.metadata["region"] == "us-east"

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            Agent(
                id="agent-bad",
                name="Bad",
                endpoint="http://x",
                status="UNKNOWN",
            )

    def test_all_statuses_accepted(self):
        for s in AGENT_STATUSES:
            agent = Agent(
                id=f"agent-{s}",
                name=f"Agent-{s}",
                endpoint="http://x",
                status=s,
            )
            assert agent.status == s

    def test_to_dict_and_from_dict_roundtrip(self):
        now = datetime.now(timezone.utc)
        agent = Agent(
            id="agent-rt",
            name="Round Trip",
            endpoint="http://rt.sam.local:5000",
            capabilities=["ping", "health"],
            status="IDLE",
            metadata={"arch": "x86_64"},
            last_heartbeat=now,
            created_at=now,
        )
        d = agent.to_dict()
        agent2 = Agent.from_dict(d)
        assert agent2.id == agent.id
        assert agent2.name == agent.name
        assert agent2.endpoint == agent.endpoint
        assert agent2.capabilities == agent.capabilities
        assert agent2.status == agent.status
        assert agent2.metadata == agent.metadata
        assert agent2.last_heartbeat is not None

    def test_from_dict_with_json_strings(self):
        d = {
            "id": "agent-js",
            "name": "JSON Agent",
            "endpoint": "http://js.local",
            "capabilities": '["cap-a", "cap-b"]',
            "status": "ONLINE",
            "metadata": '{"key": "val"}',
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        agent = Agent.from_dict(d)
        assert agent.capabilities == ["cap-a", "cap-b"]
        assert agent.metadata == {"key": "val"}

    def test_repr(self):
        agent = Agent(id="a1", name="Alpha", endpoint="http://a.local")
        r = repr(agent)
        assert "Agent(" in r
        assert "a1" in r
        assert "Alpha" in r


# ─────────────────────────────────────────────
# AgentRegistry tests
# ─────────────────────────────────────────────

class TestAgentRegistryRegister:
    @pytest.mark.asyncio
    async def test_register_agent(self, registry, db):
        agent = Agent(
            id="reg-1",
            name="Registrant",
            endpoint="http://reg.local",
            capabilities=["ping"],
        )
        await registry.register(agent)
        row = await db.fetch_one(
            "SELECT * FROM agents WHERE id = ?", (agent.id,)
        )
        assert row is not None
        assert row["name"] == "Registrant"

    @pytest.mark.asyncio
    async def test_register_overwrites_existing(self, registry, db):
        agent = Agent(
            id="reg-over",
            name="Original",
            endpoint="http://old.local",
        )
        await registry.register(agent)
        updated = Agent(
            id="reg-over",
            name="Updated",
            endpoint="http://new.local",
            capabilities=["new-cap"],
            status="BUSY",
        )
        await registry.register(updated)
        stored = await registry.get("reg-over")
        assert stored.name == "Updated"
        assert stored.endpoint == "http://new.local"
        assert stored.status == "BUSY"
        assert "new-cap" in stored.capabilities


class TestAgentRegistryGet:
    @pytest.mark.asyncio
    async def test_get_existing(self, registry):
        agent = Agent(id="get-1", name="Getter", endpoint="http://get.local")
        await registry.register(agent)
        found = await registry.get("get-1")
        assert found is not None
        assert found.name == "Getter"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, registry):
        found = await registry.get("ghost-agent")
        assert found is None


class TestAgentRegistryUnregister:
    @pytest.mark.asyncio
    async def test_unregister_existing(self, registry, db):
        agent = Agent(
            id="unreg-1", name="Unregistrant", endpoint="http://unreg.local"
        )
        await registry.register(agent)
        await registry.unregister("unreg-1")
        row = await db.fetch_one(
            "SELECT * FROM agents WHERE id = ?", ("unreg-1",)
        )
        assert row is None

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_raises(self, registry):
        with pytest.raises(ValueError, match="Agent not found"):
            await registry.unregister("ghost-agent")


class TestAgentRegistryList:
    @pytest.mark.asyncio
    async def test_list_all(self, registry):
        for i in range(3):
            await registry.register(Agent(
                id=f"list-{i}",
                name=f"Agent-{i}",
                endpoint=f"http://agent-{i}.local",
            ))
        agents = await registry.list()
        assert len(agents) == 3

    @pytest.mark.asyncio
    async def test_list_by_status(self, registry):
        await registry.register(Agent(
            id="online-1", name="Online1",
            endpoint="http://o1.local", status="ONLINE",
        ))
        await registry.register(Agent(
            id="busy-1", name="Busy1",
            endpoint="http://b1.local", status="BUSY",
        ))
        await registry.register(Agent(
            id="offline-1", name="Offline1",
            endpoint="http://f1.local", status="OFFLINE",
        ))
        online = await registry.list(status="ONLINE")
        assert len(online) == 1
        assert online[0].id == "online-1"
        busy = await registry.list(status="BUSY")
        assert len(busy) == 1
        offline = await registry.list(status="OFFLINE")
        assert len(offline) == 1

    @pytest.mark.asyncio
    async def test_list_empty(self, registry):
        agents = await registry.list()
        assert agents == []

    @pytest.mark.asyncio
    async def test_list_invalid_status_raises(self, registry):
        with pytest.raises(ValueError, match="Invalid status filter"):
            await registry.list(status="UNKNOWN")


class TestAgentRegistryHeartbeat:
    @pytest.mark.asyncio
    async def test_heartbeat_updates_timestamp_and_status(self, registry):
        agent = Agent(
            id="hb-1",
            name="Heartbeater",
            endpoint="http://hb.local",
            status="BUSY",
        )
        await registry.register(agent)
        # Wait a tiny bit so timestamp changes
        await registry.heartbeat("hb-1")
        stored = await registry.get("hb-1")
        assert stored.status == "ONLINE"
        assert stored.last_heartbeat > agent.last_heartbeat

    @pytest.mark.asyncio
    async def test_heartbeat_nonexistent_raises(self, registry):
        with pytest.raises(ValueError, match="Agent not found"):
            await registry.heartbeat("ghost-hb")


class TestAgentRegistryFindByCapability:
    @pytest.mark.asyncio
    async def test_find_by_capability(self, registry):
        await registry.register(Agent(
            id="cap-1", name="Healer",
            endpoint="http://h1.local",
            capabilities=["health-check", "repair"],
        ))
        await registry.register(Agent(
            id="cap-2", name="Scanner",
            endpoint="http://s1.local",
            capabilities=["health-check", "discovery"],
        ))
        await registry.register(Agent(
            id="cap-3", name="Deployer",
            endpoint="http://d1.local",
            capabilities=["deploy", "scale"],
        ))
        healers = await registry.find_by_capability("health-check")
        assert len(healers) == 2
        assert all("health-check" in a.capabilities for a in healers)
        deployers = await registry.find_by_capability("deploy")
        assert len(deployers) == 1
        assert deployers[0].id == "cap-3"

    @pytest.mark.asyncio
    async def test_find_by_capability_no_match(self, registry):
        await registry.register(Agent(
            id="cap-none", name="None",
            endpoint="http://n.local",
            capabilities=["ping"],
        ))
        found = await registry.find_by_capability("flying")
        assert found == []

    @pytest.mark.asyncio
    async def test_find_by_capability_exact_match_only(self, registry):
        """Ensure substring doesn't cause false positives."""
        await registry.register(Agent(
            id="cap-exact", name="Exact",
            endpoint="http://e.local",
            capabilities=["health-check"],
        ))
        # "health" should NOT match "health-check"
        found = await registry.find_by_capability("health")
        assert found == []


class TestAgentRegistryUpdateStatus:
    @pytest.mark.asyncio
    async def test_update_status(self, registry):
        agent = Agent(
            id="status-1",
            name="Status Changer",
            endpoint="http://s.local",
            status="IDLE",
        )
        await registry.register(agent)
        await registry.update_status("status-1", "BUSY")
        stored = await registry.get("status-1")
        assert stored.status == "BUSY"

    @pytest.mark.asyncio
    async def test_update_status_invalid(self, registry):
        agent = Agent(id="st-inv", name="Inv", endpoint="http://x")
        await registry.register(agent)
        with pytest.raises(ValueError, match="Invalid status"):
            await registry.update_status("st-inv", "BROKEN")

    @pytest.mark.asyncio
    async def test_update_status_nonexistent(self, registry):
        with pytest.raises(ValueError, match="Agent not found"):
            await registry.update_status("ghost-status", "BUSY")
