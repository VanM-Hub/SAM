"""
Intent Evolution – Sprint 23 Fase 3

Allows the Reasoning Engine to evolve an Intent mid-execution when
new evidence suggests the original intent is no longer appropriate.
The EvolutionManager creates a new Intent (via IntentParser) with
modified parameters and records the provenance.

Flow:
  1. Engine detects that execution evidence diverges from the original intent
  2. Calls EvolutionManager.propose_evolution()
  3. (Optional) Governance reviews the evolution
  4. Calls EvolutionManager.apply_evolution() to create a new Intent
  5. Engine creates a new ExecutionGraph for the evolved intent
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, ConfigDict
import structlog

from .intent import Intent, IntentType, IntentStatus

if TYPE_CHECKING:
    from ..persistence.database import Database
    from ..governance.engine import GovernanceEngine

logger = structlog.get_logger()


# ── Intent Evolution Model ───────────────────────────────────────────


class IntentEvolution(BaseModel):
    """Records the evolution of one Intent into another.

    Tracks the chain of evidence that triggered the change, so
    the system can audit / roll back if needed.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Unique evolution identifier (UUID)")
    original_intent_id: str = Field(description="The Intent that was evolved")
    new_intent_id: str = Field(description="The new Intent that replaced it")
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Evidence records that triggered the change",
    )
    reason: str = Field(description="Why the evolution was proposed")
    original_type: str = Field(description="Original IntentType value")
    new_type: str = Field(description="New IntentType value")
    original_target: str = Field(description="Original target")
    new_target: str = Field(description="New target")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="When the evolution was recorded",
    )


# ── Evolution Manager ────────────────────────────────────────────────


class EvolutionManager:
    """Manages intent evolution: propose, apply, history.

    Integrates with ExecutionGraphEngine when evidence shows the
    original intent is no longer suitable.
    """

    def __init__(
        self,
        db: Optional["Database"] = None,
        governance: Optional["GovernanceEngine"] = None,
    ) -> None:
        self._db = db
        self._governance = governance
        self._logger = structlog.get_logger().bind(component="EvolutionManager")

    # ── Propose ──────────────────────────────────────────────────

    async def propose_evolution(
        self,
        original_intent: Intent,
        evidence_ids: List[str],
        reason: str,
        new_intent: Optional[Intent] = None,
    ) -> IntentEvolution:
        """Propose an evolution of an intent.

        Args:
            original_intent: The current Intent being evolved.
            evidence_ids: Evidence that triggered the change.
            reason: Human-readable explanation.
            new_intent: The proposed new Intent. If not provided,
                a placeholder is created indicating the intent
                needs to be derived externally.

        Returns:
            An IntentEvolution record (not yet applied).
        """
        evolution_id = str(uuid.uuid4())

        if new_intent is None:
            new_intent = Intent(
                id=str(uuid.uuid4()),
                type=original_intent.type,
                target=original_intent.target,
                status=IntentStatus.PLANNING,
                description=reason,
            )

        evolution = IntentEvolution(
            id=evolution_id,
            original_intent_id=original_intent.id,
            new_intent_id=new_intent.id,
            evidence_ids=evidence_ids,
            reason=reason,
            original_type=original_intent.type.value,
            new_type=new_intent.type.value,
            original_target=original_intent.target,
            new_target=new_intent.target,
        )

        self._logger.info(
            "evolution.proposed",
            evolution_id=evolution_id,
            original_intent=original_intent.id,
            new_intent=new_intent.id,
            reason=reason,
            original_type=original_intent.type.value,
            new_type=new_intent.type.value,
        )

        await self._store_evolution(evolution)
        return evolution

    # ── Apply ────────────────────────────────────────────────────

    async def apply_evolution(
        self,
        evolution: IntentEvolution,
        new_intent: Intent,
    ) -> Intent:
        """Finalise an evolution by activating the new Intent.

        The new intent's status is moved to PLANNING so the
        PlanningEngine can create a new ExecutionGraph for it.

        Returns:
            The new Intent, ready for the planning phase.
        """
        new_intent.status = IntentStatus.PLANNING
        self._logger.info(
            "evolution.applied",
            evolution_id=evolution.id,
            original_intent=evolution.original_intent_id,
            new_intent=new_intent.id,
        )
        return new_intent

    # ── History ──────────────────────────────────────────────────

    async def get_evolution_history(
        self,
        intent_id: str,
        limit: int = 50,
    ) -> List[IntentEvolution]:
        """Retrieve evolution history for an intent, newest first."""
        if not self._db:
            self._logger.warning(
                "evolution.history_no_db",
                intent_id=intent_id,
            )
            return []

        try:
            rows = await self._db.fetch_all(
                """
                SELECT * FROM intent_evolutions
                WHERE original_intent_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                [intent_id, limit],
            )
        except Exception as exc:
            self._logger.warning(
                "evolution.history_failed",
                intent_id=intent_id,
                error=str(exc),
            )
            return []

        evolutions: List[IntentEvolution] = []
        for row in rows:
            evolutions.append(self._row_to_evolution(row))

        return evolutions

    # ── Internal helpers ─────────────────────────────────────────

    async def _store_evolution(self, evolution: IntentEvolution) -> None:
        """Persist an evolution record to the database."""
        if not self._db:
            self._logger.debug("evolution.not_persisted_no_db")
            return

        try:
            await self._db.execute(
                """
                INSERT OR IGNORE INTO intent_evolutions (
                    id, original_intent_id, new_intent_id,
                    evidence_ids, reason,
                    original_type, new_type,
                    original_target, new_target,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    evolution.id,
                    evolution.original_intent_id,
                    evolution.new_intent_id,
                    json.dumps(evolution.evidence_ids),
                    evolution.reason,
                    evolution.original_type,
                    evolution.new_type,
                    evolution.original_target,
                    evolution.new_target,
                    evolution.timestamp,
                ],
            )
            self._logger.debug(
                "evolution.stored",
                evolution_id=evolution.id,
                original_intent=evolution.original_intent_id,
            )
        except Exception as exc:
            self._logger.warning(
                "evolution.store_failed",
                evolution_id=evolution.id,
                error=str(exc),
            )

    def _row_to_evolution(self, row: dict) -> IntentEvolution:
        """Convert a database row to an IntentEvolution."""
        return IntentEvolution(
            id=row["id"],
            original_intent_id=row["original_intent_id"],
            new_intent_id=row["new_intent_id"],
            evidence_ids=json.loads(row["evidence_ids"]) if row.get("evidence_ids") else [],
            reason=row["reason"],
            original_type=row["original_type"],
            new_type=row["new_type"],
            original_target=row["original_target"],
            new_target=row["new_target"],
            timestamp=row["timestamp"],
        )
