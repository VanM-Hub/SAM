"""Tests for Agent Communication Protocol — Sprint 26 Fase 2.

Message model + AgentProtocol (send, send_and_wait, broadcast,
mark_delivered/read/failed, get_messages, get_pending, get_conversation).
"""

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio

from sam.persistence.database import Database
from sam.core.event_bus import EventBus
from sam.collaboration.agent import Agent
from sam.collaboration.registry import AgentRegistry
from sam.collaboration.message import (
    Message,
    MessageType,
    MessagePriority,
    MESSAGE_STATUSES,
)
from sam.collaboration.protocol import AgentProtocol


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


@pytest_asyncio.fixture
async def event_bus():
    return EventBus()


@pytest_asyncio.fixture
async def protocol(registry, event_bus, db):
    return AgentProtocol(registry, event_bus, db)


@pytest_asyncio.fixture
async def two_agents(registry):
    """Register two agents for testing."""
    a1 = Agent(id="agent-alpha", name="Alpha", endpoint="http://alpha.local",
               capabilities=["ping"], status="ONLINE")
    a2 = Agent(id="agent-beta", name="Beta", endpoint="http://beta.local",
               capabilities=["pong"], status="ONLINE")
    await registry.register(a1)
    await registry.register(a2)
    return {"alpha": a1, "beta": a2}


# ─────────────────────────────────────────────
# Message model tests
# ─────────────────────────────────────────────

class TestMessageModel:
    def test_create_minimal(self):
        msg = Message(
            id="msg-1",
            type=MessageType.REQUEST,
            sender_id="agent-alpha",
            payload={"action": "ping"},
        )
        assert msg.id == "msg-1"
        assert msg.type == MessageType.REQUEST
        assert msg.sender_id == "agent-alpha"
        assert msg.receiver_id is None
        assert msg.correlation_id == "msg-1"  # defaults to id
        assert msg.priority == MessagePriority.NORMAL
        assert msg.status == "SENT"

    def test_create_with_all_fields(self):
        msg = Message(
            id="msg-full",
            type=MessageType.RESPONSE,
            sender_id="agent-alpha",
            receiver_id="agent-beta",
            correlation_id="corr-001",
            priority=MessagePriority.HIGH,
            payload={"result": "ok"},
            timestamp=datetime.now(timezone.utc),
            status="DELIVERED",
        )
        assert msg.type == MessageType.RESPONSE
        assert msg.receiver_id == "agent-beta"
        assert msg.correlation_id == "corr-001"
        assert msg.priority == MessagePriority.HIGH
        assert msg.status == "DELIVERED"

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            Message(id="bad", type=MessageType.REQUEST, sender_id="a",
                    payload={}, status="UNKNOWN")

    def test_all_statuses_accepted(self):
        for s in MESSAGE_STATUSES:
            msg = Message(id=f"msg-{s}", type=MessageType.REQUEST,
                          sender_id="a", payload={}, status=s)
            assert msg.status == s

    def test_message_type_enum_values(self):
        assert MessageType.REQUEST.value == "REQUEST"
        assert MessageType.RESPONSE.value == "RESPONSE"
        assert MessageType.BROADCAST.value == "BROADCAST"
        assert MessageType.KNOWLEDGE_SHARE.value == "KNOWLEDGE_SHARE"
        assert MessageType.TASK_DELEGATE.value == "TASK_DELEGATE"
        assert MessageType.HEARTBEAT.value == "HEARTBEAT"
        assert MessageType.ERROR.value == "ERROR"

    def test_message_priority_enum_values(self):
        assert MessagePriority.LOW.value == "LOW"
        assert MessagePriority.NORMAL.value == "NORMAL"
        assert MessagePriority.HIGH.value == "HIGH"
        assert MessagePriority.CRITICAL.value == "CRITICAL"

    def test_to_dict_and_from_dict_roundtrip(self):
        msg = Message(
            id="msg-rt",
            type=MessageType.KNOWLEDGE_SHARE,
            sender_id="agent-alpha",
            receiver_id="agent-beta",
            correlation_id="corr-999",
            priority=MessagePriority.CRITICAL,
            payload={"knowledge": ["fact-1", "fact-2"]},
            timestamp=datetime.now(timezone.utc),
            status="READ",
        )
        d = msg.to_dict()
        msg2 = Message.from_dict(d)
        assert msg2.id == msg.id
        assert msg2.type == msg.type
        assert msg2.sender_id == msg.sender_id
        assert msg2.receiver_id == msg.receiver_id
        assert msg2.correlation_id == msg.correlation_id
        assert msg2.priority == msg.priority
        assert msg2.payload == msg.payload
        assert msg2.status == msg.status

    def test_from_dict_with_json_strings(self):
        d = {
            "id": "msg-js",
            "type": "ERROR",
            "sender_id": "agent-alpha",
            "receiver_id": "agent-beta",
            "correlation_id": "corr-js",
            "priority": "LOW",
            "payload": '{"error": "timeout"}',
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "FAILED",
        }
        msg = Message.from_dict(d)
        assert msg.type == MessageType.ERROR
        assert msg.priority == MessagePriority.LOW
        assert msg.payload == {"error": "timeout"}
        assert msg.status == "FAILED"

    def test_broadcast_has_no_receiver(self):
        msg = Message(
            id="msg-bc",
            type=MessageType.BROADCAST,
            sender_id="agent-alpha",
            payload={"announcement": "hello all"},
        )
        assert msg.receiver_id is None
        d = msg.to_dict()
        assert d["receiver_id"] is None

    def test_repr(self):
        msg = Message(id="m1", type=MessageType.REQUEST,
                      sender_id="a", payload={})
        r = repr(msg)
        assert "Message(" in r
        assert "m1" in r
        assert "REQUEST" in r


# ─────────────────────────────────────────────
# AgentProtocol tests
# ─────────────────────────────────────────────

class TestAgentProtocolSend:
    @pytest.mark.asyncio
    async def test_send_direct_message(self, protocol, two_agents, db):
        msg = Message(
            id="send-1",
            type=MessageType.REQUEST,
            sender_id="agent-alpha",
            receiver_id="agent-beta",
            payload={"query": "status"},
        )
        msg_id = await protocol.send(msg)
        assert msg_id == "send-1"
        row = await db.fetch_one(
            "SELECT * FROM messages WHERE id = ?", (msg_id,)
        )
        assert row is not None
        assert row["status"] == "SENT"

    @pytest.mark.asyncio
    async def test_send_nonexistent_sender_raises(self, protocol, two_agents):
        msg = Message(
            id="send-bad",
            type=MessageType.REQUEST,
            sender_id="ghost",
            receiver_id="agent-beta",
            payload={},
        )
        with pytest.raises(ValueError, match="Sender agent not found"):
            await protocol.send(msg)

    @pytest.mark.asyncio
    async def test_send_nonexistent_receiver_raises(self, protocol, two_agents):
        msg = Message(
            id="send-bad-r",
            type=MessageType.REQUEST,
            sender_id="agent-alpha",
            receiver_id="ghost",
            payload={},
        )
        with pytest.raises(ValueError, match="Receiver agent not found"):
            await protocol.send(msg)

    @pytest.mark.asyncio
    async def test_send_knowledge_share(self, protocol, two_agents):
        msg = Message(
            id="send-ks",
            type=MessageType.KNOWLEDGE_SHARE,
            sender_id="agent-alpha",
            receiver_id="agent-beta",
            payload={"knowledge_item": "inst-mem-42"},
        )
        msg_id = await protocol.send(msg)
        assert msg_id == "send-ks"


class TestAgentProtocolMarkDelivered:
    @pytest.mark.asyncio
    async def test_mark_delivered(self, protocol, two_agents):
        msg = Message(
            id="md-1", type=MessageType.REQUEST,
            sender_id="agent-alpha", receiver_id="agent-beta",
            payload={},
        )
        await protocol.send(msg)
        await protocol.mark_delivered("md-1")
        row = await protocol.db.fetch_one(
            "SELECT status FROM messages WHERE id = ?", ("md-1",)
        )
        assert row["status"] == "DELIVERED"

    @pytest.mark.asyncio
    async def test_mark_delivered_nonexistent_raises(self, protocol):
        with pytest.raises(ValueError, match="Message not found"):
            await protocol.mark_delivered("ghost-msg")


class TestAgentProtocolMarkRead:
    @pytest.mark.asyncio
    async def test_mark_read(self, protocol, two_agents):
        msg = Message(
            id="mr-1", type=MessageType.REQUEST,
            sender_id="agent-alpha", receiver_id="agent-beta",
            payload={},
        )
        await protocol.send(msg)
        await protocol.mark_read("mr-1")
        row = await protocol.db.fetch_one(
            "SELECT status FROM messages WHERE id = ?", ("mr-1",)
        )
        assert row["status"] == "READ"

    @pytest.mark.asyncio
    async def test_mark_read_nonexistent_raises(self, protocol):
        with pytest.raises(ValueError, match="Message not found"):
            await protocol.mark_read("ghost-msg")


class TestAgentProtocolMarkFailed:
    @pytest.mark.asyncio
    async def test_mark_failed(self, protocol, two_agents):
        msg = Message(
            id="mf-1", type=MessageType.REQUEST,
            sender_id="agent-alpha", receiver_id="agent-beta",
            payload={},
        )
        await protocol.send(msg)
        await protocol.mark_failed("mf-1")
        row = await protocol.db.fetch_one(
            "SELECT status FROM messages WHERE id = ?", ("mf-1",)
        )
        assert row["status"] == "FAILED"

    @pytest.mark.asyncio
    async def test_mark_failed_nonexistent_raises(self, protocol):
        with pytest.raises(ValueError, match="Message not found"):
            await protocol.mark_failed("ghost-msg")


class TestAgentProtocolGetMessages:
    @pytest.mark.asyncio
    async def test_get_messages_for_agent(self, protocol, two_agents):
        await protocol.send(Message(
            id="gm-1", type=MessageType.REQUEST,
            sender_id="agent-alpha", receiver_id="agent-beta",
            payload={"seq": 1},
        ))
        await protocol.send(Message(
            id="gm-2", type=MessageType.RESPONSE,
            sender_id="agent-beta", receiver_id="agent-alpha",
            payload={"seq": 2},
        ))
        msgs = await protocol.get_messages("agent-alpha")
        assert len(msgs) >= 2

    @pytest.mark.asyncio
    async def test_get_messages_limit(self, protocol, two_agents):
        for i in range(5):
            await protocol.send(Message(
                id=f"gm-limit-{i}", type=MessageType.REQUEST,
                sender_id="agent-alpha", receiver_id="agent-beta",
                payload={"i": i},
            ))
        msgs = await protocol.get_messages("agent-alpha", limit=3)
        assert len(msgs) == 3

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, protocol):
        msgs = await protocol.get_messages("ghost-agent")
        assert msgs == []


class TestAgentProtocolGetPending:
    @pytest.mark.asyncio
    async def test_get_pending_messages(self, protocol, two_agents):
        await protocol.send(Message(
            id="pending-1", type=MessageType.REQUEST,
            sender_id="agent-alpha", receiver_id="agent-beta",
            payload={},
        ))
        await protocol.send(Message(
            id="pending-2", type=MessageType.REQUEST,
            sender_id="agent-alpha", receiver_id="agent-beta",
            payload={},
        ))
        pending = await protocol.get_pending("agent-beta")
        assert len(pending) == 2
        assert all(m.status == "SENT" for m in pending)

    @pytest.mark.asyncio
    async def test_get_pending_after_delivery(self, protocol, two_agents):
        await protocol.send(Message(
            id="pending-d1", type=MessageType.REQUEST,
            sender_id="agent-alpha", receiver_id="agent-beta",
            payload={},
        ))
        await protocol.mark_delivered("pending-d1")
        pending = await protocol.get_pending("agent-beta")
        assert len(pending) == 0


class TestAgentProtocolGetConversation:
    @pytest.mark.asyncio
    async def test_get_conversation(self, protocol, two_agents):
        await protocol.send(Message(
            id="conv-1", type=MessageType.REQUEST,
            sender_id="agent-alpha", receiver_id="agent-beta",
            payload={"q": "hello"},
        ))
        await protocol.send(Message(
            id="conv-2", type=MessageType.RESPONSE,
            sender_id="agent-beta", receiver_id="agent-alpha",
            payload={"a": "hi"},
        ))
        conv = await protocol.get_conversation("agent-alpha", "agent-beta")
        assert len(conv) == 2
        assert conv[0].id == "conv-1"  # oldest first
        assert conv[1].id == "conv-2"


class TestAgentProtocolSendAndWait:
    @pytest.mark.asyncio
    async def test_send_and_wait_gets_response(self, protocol, two_agents):
        async def responder():
            # Simulate agent-beta responding
            response = Message(
                id="resp-1",
                type=MessageType.RESPONSE,
                sender_id="agent-beta",
                receiver_id="agent-alpha",
                correlation_id="corr-sw-1",
                payload={"status": "ok"},
            )
            await protocol.deliver_response(response)

        request = Message(
            id="req-sw-1",
            type=MessageType.REQUEST,
            sender_id="agent-alpha",
            receiver_id="agent-beta",
            correlation_id="corr-sw-1",
            payload={"action": "ping"},
        )

        # Fire responder with slight delay
        async def delayed_responder():
            await asyncio.sleep(0.05)
            await responder()

        asyncio.create_task(delayed_responder())
        response = await protocol.send_and_wait(request, timeout=5)
        assert response.type == MessageType.RESPONSE
        assert response.correlation_id == "corr-sw-1"
        assert response.payload == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_send_and_wait_timeout(self, protocol, two_agents):
        request = Message(
            id="req-timeout",
            type=MessageType.REQUEST,
            sender_id="agent-alpha",
            receiver_id="agent-beta",
            correlation_id="corr-timeout",
            payload={"action": "ping"},
        )
        with pytest.raises(asyncio.TimeoutError):
            await protocol.send_and_wait(request, timeout=0.1)

    @pytest.mark.asyncio
    async def test_send_and_wait_no_response_future_cleanup(self, protocol, two_agents):
        """After timeout, future is cleaned up from _pending_responses."""
        request = Message(
            id="req-clean",
            type=MessageType.REQUEST,
            sender_id="agent-alpha",
            receiver_id="agent-beta",
            correlation_id="corr-clean",
            payload={},
        )
        assert "corr-clean" not in protocol._pending_responses
        with pytest.raises(asyncio.TimeoutError):
            await protocol.send_and_wait(request, timeout=0.1)
        assert "corr-clean" not in protocol._pending_responses


class TestAgentProtocolBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_online(self, protocol, two_agents, db):
        msg = Message(
            id="bc-1",
            type=MessageType.BROADCAST,
            sender_id="agent-alpha",
            payload={"alert": "system update"},
        )
        sent_ids = await protocol.broadcast(msg)
        # One master + one for beta (alpha skips self)
        assert len(sent_ids) >= 2

        all_msgs = await db.fetch_all("SELECT * FROM messages")
        broadcast_msgs = [r for r in all_msgs if r["id"] in sent_ids]
        assert len(broadcast_msgs) >= 2

    @pytest.mark.asyncio
    async def test_broadcast_skips_self(self, protocol, two_agents):
        msg = Message(
            id="bc-self",
            type=MessageType.BROADCAST,
            sender_id="agent-alpha",
            payload={"msg": "test"},
        )
        sent_ids = await protocol.broadcast(msg)
        # Should not be a message to agent-alpha from agent-alpha
        rows = await protocol.db.fetch_all(
            "SELECT * FROM messages WHERE id = ?", ("bc-self",)
        )
        assert len(rows) == 1  # only the master broadcast
        assert rows[0]["receiver_id"] is None

    @pytest.mark.asyncio
    async def test_broadcast_no_online_agents(self, protocol, registry):
        agent = Agent(id="alone", name="Lonely", endpoint="http://a.local")
        await registry.register(agent)
        msg = Message(
            id="bc-alone",
            type=MessageType.BROADCAST,
            sender_id="alone",
            payload={},
        )
        sent_ids = await protocol.broadcast(msg)
        assert len(sent_ids) == 1  # just the master broadcast


class TestAgentProtocolFullLifecycle:
    @pytest.mark.asyncio
    async def test_full_message_lifecycle(self, protocol, two_agents):
        """SENT → DELIVERED → READ."""
        msg = Message(
            id="lifecycle-1",
            type=MessageType.REQUEST,
            sender_id="agent-alpha",
            receiver_id="agent-beta",
            payload={"task": "health_check"},
        )
        await protocol.send(msg)
        assert (await protocol._get_or_raise("lifecycle-1")).status == "SENT"

        await protocol.mark_delivered("lifecycle-1")
        assert (await protocol._get_or_raise("lifecycle-1")).status == "DELIVERED"

        await protocol.mark_read("lifecycle-1")
        assert (await protocol._get_or_raise("lifecycle-1")).status == "READ"

    @pytest.mark.asyncio
    async def test_send_fail_lifecycle(self, protocol, two_agents):
        """SENT → FAILED."""
        msg = Message(
            id="fail-1",
            type=MessageType.REQUEST,
            sender_id="agent-alpha",
            receiver_id="agent-beta",
            payload={},
        )
        await protocol.send(msg)
        await protocol.mark_failed("fail-1")
        assert (await protocol._get_or_raise("fail-1")).status == "FAILED"

    @pytest.mark.asyncio
    async def test_send_error_message(self, protocol, two_agents):
        msg = Message(
            id="err-1",
            type=MessageType.ERROR,
            sender_id="agent-beta",
            receiver_id="agent-alpha",
            payload={"error": "timeout", "original_request": "req-42"},
            correlation_id="corr-err",
        )
        msg_id = await protocol.send(msg)
        assert msg_id == "err-1"
        stored = await protocol._get_or_raise("err-1")
        assert stored.type == MessageType.ERROR
