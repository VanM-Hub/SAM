"""Agent Communication Protocol — Sprint 26 Fase 2.

Async-first protocol for inter-agent messaging with:
- Send / Send-and-Wait (with timeout) / Broadcast
- Message persistence and audit trail
- Status tracking (SENT → DELIVERED → READ / FAILED)
- Event-driven notification via EventBus
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.core.event_bus import EventBus
from sam.core.events import Event
from sam.persistence.database import Database
from .agent import Agent
from .message import Message, MessagePriority, MessageType
from .registry import AgentRegistry


logger = structlog.get_logger()

# Events emitted by the protocol
MESSAGE_SENT = "agent.message.sent"
MESSAGE_DELIVERED = "agent.message.delivered"
MESSAGE_READ = "agent.message.read"
MESSAGE_FAILED = "agent.message.failed"


class AgentProtocol:
    """Async-first communication protocol for multi-agent collaboration.

    Provides reliable message delivery with retry, timeout, audit trail,
    and EventBus notifications.

    Args:
        registry: AgentRegistry for agent lookups.
        event_bus: EventBus for publishing message lifecycle events.
        db: Database for persistent message storage.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        event_bus: EventBus,
        db: Database,
    ) -> None:
        self.registry = registry
        self.event_bus = event_bus
        self.db = db
        self.logger = logger.bind(component="AgentProtocol")
        self._pending_responses: Dict[str, asyncio.Future] = {}

    # ── Core send ────────────────────────────────────────────────

    async def send(self, message: Message) -> str:
        """Send a message to its destination agent.

        Persists the message, publishes MESSAGE_SENT event,
        and for direct messages attempts immediate delivery.

        Args:
            message: The Message to send.

        Returns:
            The message ID.

        Raises:
            ValueError: If the sender agent does not exist.
            ValueError: If receiver_id is set but agent does not exist.
        """
        # Validate sender exists
        sender = await self.registry.get(message.sender_id)
        if sender is None:
            raise ValueError(f"Sender agent not found: {message.sender_id}")

        # Validate receiver exists (if specified)
        if message.receiver_id is not None:
            receiver = await self.registry.get(message.receiver_id)
            if receiver is None:
                raise ValueError(
                    f"Receiver agent not found: {message.receiver_id}"
                )

        d = message.to_dict()
        await self.db.execute(
            """INSERT INTO messages
               (id, type, sender_id, receiver_id, correlation_id,
                priority, payload, timestamp, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["type"], d["sender_id"], d["receiver_id"],
                d["correlation_id"], d["priority"], d["payload"],
                d["timestamp"], d["status"],
            ),
        )

        # Publish event
        await self.event_bus.publish(Event(
            id=str(uuid.uuid4()),
            type=MESSAGE_SENT,
            source="AgentProtocol.send",
            payload={"message_id": message.id, "type": message.type.value},
        ))

        self.logger.info(
            "Message sent",
            message_id=message.id,
            msg_type=message.type.value,
            sender=message.sender_id,
            receiver=message.receiver_id,
        )
        return message.id

    # ── Send and wait ────────────────────────────────────────────

    async def send_and_wait(
        self,
        message: Message,
        timeout: int = 30,
    ) -> Message:
        """Send a message and wait for a correlated response.

        Creates a pending future keyed by correlation_id, sends the message,
        then awaits a RESPONSE with matching correlation_id.

        Args:
            message: The Message to send (should be MessageType.REQUEST).
            timeout: Maximum seconds to wait for a response.

        Returns:
            The response Message.

        Raises:
            asyncio.TimeoutError: If no response arrives within timeout.
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        correlation_id = message.correlation_id
        self._pending_responses[correlation_id] = future

        try:
            await self.send(message)
            # Wait with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        finally:
            self._pending_responses.pop(correlation_id, None)

    # ── Deliver response (called by receiver) ────────────────────

    async def deliver_response(self, response: Message) -> None:
        """Deliver a RESPONSE message, resolving a pending send_and_wait.

        If there's a pending future matching the correlation_id, it is
        resolved. Otherwise the message is persisted normally.

        Args:
            response: The response Message.
        """
        # Resolve pending future if exists
        future = self._pending_responses.get(response.correlation_id)
        if future is not None and not future.done():
            await self.send(response)
            future.set_result(response)
            return

        # No pending future — persist as regular message
        await self.send(response)

    # ── Broadcast ────────────────────────────────────────────────

    async def broadcast(self, message: Message) -> List[str]:
        """Broadcast a message to all ONLINE agents.

        The message's receiver_id is set to None (broadcast).
        Each agent receives a copy of the payload.

        Args:
            message: The Message to broadcast.

        Returns:
            List of sent message IDs (one per receiver + one master).
        """
        sent_ids: List[str] = []
        agents = await self.registry.list(status="ONLINE")

        # Send the broadcast message itself (receiver_id = None)
        broadcast_msg = Message(
            id=message.id,
            type=MessageType.BROADCAST,
            sender_id=message.sender_id,
            receiver_id=None,
            correlation_id=message.correlation_id,
            priority=message.priority,
            payload=message.payload,
        )
        await self.send(broadcast_msg)
        sent_ids.append(broadcast_msg.id)

        # Send individual copies to each online agent
        for agent in agents:
            if agent.id == message.sender_id:
                continue  # Don't send to yourself
            individual = Message(
                id=str(uuid.uuid4()),
                type=MessageType.BROADCAST,
                sender_id=message.sender_id,
                receiver_id=agent.id,
                correlation_id=message.correlation_id,
                priority=message.priority,
                payload=message.payload,
            )
            await self.send(individual)
            sent_ids.append(individual.id)

        self.logger.info(
            "Broadcast sent",
            message_id=message.id,
            sender=message.sender_id,
            targets=len(agents),
        )
        return sent_ids

    # ── Status transitions ───────────────────────────────────────

    async def mark_delivered(self, message_id: str) -> None:
        """Mark a message as DELIVERED.

        Args:
            message_id: The message to update.

        Raises:
            ValueError: If message does not exist.
        """
        msg = await self._get_or_raise(message_id)
        await self.db.execute(
            "UPDATE messages SET status = 'DELIVERED' WHERE id = ?",
            (message_id,),
        )
        await self.event_bus.publish(Event(
            id=str(uuid.uuid4()),
            type=MESSAGE_DELIVERED,
            source="AgentProtocol.mark_delivered",
            payload={"message_id": message_id},
        ))

    async def mark_read(self, message_id: str) -> None:
        """Mark a message as READ.

        Args:
            message_id: The message to update.

        Raises:
            ValueError: If message does not exist.
        """
        msg = await self._get_or_raise(message_id)
        await self.db.execute(
            "UPDATE messages SET status = 'READ' WHERE id = ?",
            (message_id,),
        )
        await self.event_bus.publish(Event(
            id=str(uuid.uuid4()),
            type=MESSAGE_READ,
            source="AgentProtocol.mark_read",
            payload={"message_id": message_id},
        ))

    async def mark_failed(self, message_id: str) -> None:
        """Mark a message as FAILED.

        Args:
            message_id: The message to update.

        Raises:
            ValueError: If message does not exist.
        """
        msg = await self._get_or_raise(message_id)
        await self.db.execute(
            "UPDATE messages SET status = 'FAILED' WHERE id = ?",
            (message_id,),
        )
        await self.event_bus.publish(Event(
            id=str(uuid.uuid4()),
            type=MESSAGE_FAILED,
            source="AgentProtocol.mark_failed",
            payload={"message_id": message_id},
        ))

    # ── Query ────────────────────────────────────────────────────

    async def get_messages(
        self, agent_id: str, limit: int = 50
    ) -> List[Message]:
        """Get messages for an agent (sent or received).

        Args:
            agent_id: The agent ID.
            limit: Maximum messages to return.

        Returns:
            List of Message objects, newest first.
        """
        rows = await self.db.fetch_all(
            """SELECT * FROM messages
               WHERE sender_id = ? OR receiver_id = ? OR receiver_id IS NULL
               ORDER BY timestamp DESC LIMIT ?""",
            (agent_id, agent_id, limit),
        )
        return [Message.from_dict(dict(r)) for r in rows]

    async def get_pending(self, agent_id: str) -> List[Message]:
        """Get pending (SENT) messages for an agent.

        These are messages addressed to agent_id that have not yet been
        delivered or read. Excludes broadcasts to ensure only targeted
        messages appear as pending.

        Args:
            agent_id: The agent ID.

        Returns:
            List of pending Message objects, oldest first.
        """
        rows = await self.db.fetch_all(
            """SELECT * FROM messages
               WHERE receiver_id = ? AND status = 'SENT'
               ORDER BY timestamp ASC""",
            (agent_id,),
        )
        return [Message.from_dict(dict(r)) for r in rows]

    async def get_conversation(
        self, agent_a: str, agent_b: str, limit: int = 50
    ) -> List[Message]:
        """Get the conversation between two agents.

        Returns messages where (sender=A AND receiver=B) OR (sender=B AND receiver=A),
        ordered by timestamp ascending (oldest first).

        Args:
            agent_a: First agent ID.
            agent_b: Second agent ID.
            limit: Maximum messages to return.

        Returns:
            List of Message objects.
        """
        rows = await self.db.fetch_all(
            """SELECT * FROM messages
               WHERE (sender_id = ? AND receiver_id = ?)
                  OR (sender_id = ? AND receiver_id = ?)
               ORDER BY timestamp ASC LIMIT ?""",
            (agent_a, agent_b, agent_b, agent_a, limit),
        )
        return [Message.from_dict(dict(r)) for r in rows]

    # ── Internal helpers ─────────────────────────────────────────

    async def _get_or_raise(self, message_id: str) -> Message:
        row = await self.db.fetch_one(
            "SELECT * FROM messages WHERE id = ?", (message_id,)
        )
        if row is None:
            raise ValueError(f"Message not found: {message_id}")
        return Message.from_dict(dict(row))
