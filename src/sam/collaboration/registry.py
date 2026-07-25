"""Agent Registry — Sprint 26 Fase 1.

Manages agent registration, discovery, heartbeat tracking,
and capability-based lookup for the SAM collaboration ecosystem.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database
from .agent import Agent


logger = structlog.get_logger()


class AgentRegistry:
    """Registry for discovering and managing agents in the SAM ecosystem.

    Provides CRUD, status tracking, heartbeat monitoring, and
    capability-based lookup.
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logger.bind(component="AgentRegistry")

    async def register(self, agent: Agent) -> None:
        """Register a new agent or update an existing one.

        Uses INSERT OR REPLACE so the same agent_id always
        corresponds to the same agent.

        Args:
            agent: The Agent to register.
        """
        d = agent.to_dict()
        await self.db.execute(
            """INSERT OR REPLACE INTO agents
               (id, name, capabilities, status, endpoint, metadata,
                last_heartbeat, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["name"], d["capabilities"], d["status"],
                d["endpoint"], d["metadata"], d["last_heartbeat"],
                d["created_at"], d["last_heartbeat"],
            ),
        )
        self.logger.info(
            "Agent registered",
            agent_id=agent.id,
            name=agent.name,
            status=agent.status,
        )

    async def unregister(self, agent_id: str) -> None:
        """Unregister an agent by ID.

        Args:
            agent_id: The agent ID to remove.

        Raises:
            ValueError: If agent does not exist.
        """
        existing = await self.get(agent_id)
        if existing is None:
            raise ValueError(f"Agent not found: {agent_id}")
        await self.db.execute(
            "DELETE FROM agents WHERE id = ?", (agent_id,)
        )
        self.logger.info("Agent unregistered", agent_id=agent_id)

    async def get(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID.

        Args:
            agent_id: The agent ID to look up.

        Returns:
            The Agent if found, or None.
        """
        row = await self.db.fetch_one(
            "SELECT * FROM agents WHERE id = ?", (agent_id,)
        )
        if row is None:
            return None
        return Agent.from_dict(dict(row))

    async def list(self, status: Optional[str] = None) -> List[Agent]:
        """List all registered agents, optionally filtered by status.

        Args:
            status: If set, only return agents with this status.

        Returns:
            List of matching Agent objects.
        """
        if status is not None:
            if status not in {"ONLINE", "OFFLINE", "BUSY", "IDLE"}:
                raise ValueError(f"Invalid status filter: '{status}'")
            rows = await self.db.fetch_all(
                "SELECT * FROM agents WHERE status = ? ORDER BY name",
                (status,),
            )
        else:
            rows = await self.db.fetch_all(
                "SELECT * FROM agents ORDER BY name"
            )
        return [Agent.from_dict(dict(r)) for r in rows]

    async def heartbeat(self, agent_id: str) -> None:
        """Record a heartbeat for an agent, updating its timestamp and
        setting status to ONLINE.

        Args:
            agent_id: The agent sending the heartbeat.

        Raises:
            ValueError: If agent does not exist.
        """
        existing = await self.get(agent_id)
        if existing is None:
            raise ValueError(f"Agent not found: {agent_id}")
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE agents SET last_heartbeat = ?, status = 'ONLINE', "
            "updated_at = ? WHERE id = ?",
            (now, now, agent_id),
        )
        self.logger.debug("Heartbeat recorded", agent_id=agent_id)

    async def find_by_capability(self, capability: str) -> List[Agent]:
        """Find agents that have a specific capability.

        Searches inside the JSON-encoded capabilities list.

        Args:
            capability: The capability string to search for.

        Returns:
            List of matching Agent objects.
        """
        # Use LIKE with JSON array pattern: capability may appear anywhere
        # in the array representation
        pattern = f"%{capability}%"
        rows = await self.db.fetch_all(
            "SELECT * FROM agents WHERE capabilities LIKE ? ORDER BY name",
            (pattern,),
        )
        # Post-filter to ensure exact match (avoid substring false positives)
        result = []
        for row in rows:
            agent = Agent.from_dict(dict(row))
            if capability in agent.capabilities:
                result.append(agent)
        return result

    async def update_status(self, agent_id: str, status: str) -> None:
        """Update an agent's operational status.

        Args:
            agent_id: The agent to update.
            status: New status (ONLINE, OFFLINE, BUSY, IDLE).

        Raises:
            ValueError: If agent does not exist or status invalid.
        """
        if status not in {"ONLINE", "OFFLINE", "BUSY", "IDLE"}:
            raise ValueError(f"Invalid status: '{status}'")
        existing = await self.get(agent_id)
        if existing is None:
            raise ValueError(f"Agent not found: {agent_id}")
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE agents SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, agent_id),
        )
        self.logger.info("Agent status updated", agent_id=agent_id, status=status)
