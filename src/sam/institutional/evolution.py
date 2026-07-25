"""Template Evolution — Sprint 25 Fase 2.

Evaluates Graph Templates based on historical success/failure data from
Institutional Memory, proposes improvements, manages the approval lifecycle,
applies or rollbacks changes.

Lifecycle: PROPOSED → APPROVED → APPLIED → (ROLLED_BACK)
Or: PROPOSED → REJECTED
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()


EVOLUTION_STATUSES = frozenset({
    "PROPOSED", "APPROVED", "REJECTED", "APPLIED", "ROLLED_BACK",
})

MIN_EVALUATION_EXECUTIONS = 3
"""Minimum number of historical executions needed before proposing an evolution."""


class TemplateEvolution:
    """A proposal to evolve a Graph Template.

    Carries the original and new version, a list of changes,
    reason for the change, supporting evidence, and a status
    that progresses through a lifecycle.
    """

    def __init__(
        self,
        id: str,
        template_id: str,
        original_version: str,
        new_version: str,
        changes: Optional[List[Dict[str, Any]]] = None,
        reason: str = "",
        evidence: Optional[List[str]] = None,
        status: str = "PROPOSED",
        proposed_at: Optional[datetime] = None,
        applied_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if status not in EVOLUTION_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of {sorted(EVOLUTION_STATUSES)}"
            )
        self.id = id
        self.template_id = template_id
        self.original_version = original_version
        self.new_version = new_version
        self.changes = changes or []
        self.reason = reason
        self.evidence = evidence or []
        self.status = status
        now = datetime.now(timezone.utc)
        self.proposed_at = proposed_at or now
        self.applied_at = applied_at
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "template_id": self.template_id,
            "original_version": self.original_version,
            "new_version": self.new_version,
            "changes": json.dumps(self.changes),
            "reason": self.reason,
            "evidence": json.dumps(self.evidence),
            "status": self.status,
            "proposed_at": self.proposed_at.isoformat(),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TemplateEvolution:
        return cls(
            id=data["id"],
            template_id=data["template_id"],
            original_version=data["original_version"],
            new_version=data["new_version"],
            changes=_parse_json_list_dict(data.get("changes", "[]")),
            reason=data.get("reason", ""),
            evidence=_parse_json_list_str(data.get("evidence", "[]")),
            status=data.get("status", "PROPOSED"),
            proposed_at=_parse_dt(data.get("proposed_at")),
            applied_at=_parse_dt(data.get("applied_at")),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
        )

    def __repr__(self) -> str:
        return (
            f"TemplateEvolution(id={self.id!r}, template_id={self.template_id!r}, "
            f"status={self.status!r}, {self.original_version}→{self.new_version})"
        )


def _parse_json_list_dict(val: Any) -> List[Dict[str, Any]]:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    try:
        parsed = json.loads(val)
        return parsed if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []


def _parse_json_list_str(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val]
    try:
        parsed = json.loads(val)
        return [str(v) for v in parsed] if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class TemplateEvolutionManager:
    """Manages template evaluation, proposal, approval, apply, and rollback."""

    def __init__(self, db: Database, memory_manager: Any = None) -> None:
        self.db = db
        self.memory_manager = memory_manager
        self.logger = logger.bind(component="TemplateEvolutionManager")

    # ── Evaluation ────────────────────────────────────────────────

    async def evaluate_template(
        self, template_id: str
    ) -> Dict[str, Any]:
        """Evaluate a template's performance using Institutional Memory data.

        Returns:
            Dict with keys: template_id, success_rate, failure_rate,
            total_executions, avg_confidence, has_sufficient_data,
            recommendation.
        """
        result: Dict[str, Any] = {
            "template_id": template_id,
            "success_rate": 0.0,
            "failure_rate": 0.0,
            "total_executions": 0,
            "avg_confidence": 0.0,
            "has_sufficient_data": False,
            "recommendation": "insufficient_data",
        }

        if self.memory_manager is None:
            return result

        # Query institutional memory for entries sourced from this template
        memories = await self.memory_manager.search({"source": template_id})

        total = len(memories)
        result["total_executions"] = total

        if total == 0:
            return result

        if total < MIN_EVALUATION_EXECUTIONS:
            return result

        result["has_sufficient_data"] = True

        successes = sum(1 for m in memories if m.success_count > m.failure_count)
        failures = total - successes
        result["success_rate"] = successes / total
        result["failure_rate"] = failures / total
        result["avg_confidence"] = (
            sum(m.confidence for m in memories) / total
        )

        if result["success_rate"] >= 0.8:
            result["recommendation"] = "stable"
        elif result["success_rate"] >= 0.5:
            result["recommendation"] = "needs_review"
        else:
            result["recommendation"] = "needs_improvement"

        return result

    # ── Proposal ──────────────────────────────────────────────────

    async def propose_evolution(
        self,
        template_id: str,
        changes: List[Dict[str, Any]],
        reason: str,
        original_version: str = "1.0",
        new_version: str = "2.0",
    ) -> TemplateEvolution:
        """Propose an evolution for a template.

        Creates a PROPOSED TemplateEvolution entry.

        Returns:
            The newly created TemplateEvolution.
        """
        now = datetime.now(timezone.utc)
        evolution = TemplateEvolution(
            id=str(uuid.uuid4()),
            template_id=template_id,
            original_version=original_version,
            new_version=new_version,
            changes=changes,
            reason=reason,
            evidence=[],
            status="PROPOSED",
            proposed_at=now,
            created_at=now,
            updated_at=now,
        )
        d = evolution.to_dict()
        await self.db.execute(
            """INSERT INTO template_evolutions
               (id, template_id, original_version, new_version,
                changes, reason, evidence, status,
                proposed_at, applied_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["template_id"], d["original_version"],
                d["new_version"], d["changes"], d["reason"],
                d["evidence"], d["status"], d["proposed_at"],
                d["applied_at"], d["created_at"], d["updated_at"],
            ),
        )
        self.logger.info(
            "Evolution proposed",
            evolution_id=evolution.id,
            template_id=template_id,
            reason=reason,
        )
        return evolution

    # ── Approval ──────────────────────────────────────────────────

    async def approve_evolution(self, evolution_id: str) -> None:
        """Approve a PROPOSED evolution, transitioning to APPROVED."""
        evo = await self._get_or_raise(evolution_id)
        if evo.status != "PROPOSED":
            raise ValueError(
                f"Cannot approve evolution {evolution_id}: "
                f"current status is '{evo.status}', expected 'PROPOSED'"
            )
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE template_evolutions SET status = 'APPROVED', "
            "updated_at = ? WHERE id = ?",
            (now, evolution_id),
        )
        self.logger.info(
            "Evolution approved",
            evolution_id=evolution_id,
        )

    # ── Apply ─────────────────────────────────────────────────────

    async def apply_evolution(self, evolution_id: str) -> None:
        """Apply an APPROVED evolution.

        Transitions status to APPLIED and records applied_at.
        Note: actual template mutation is delegated to the caller
        (e.g., PlanningEngine); this method manages the record only.
        """
        evo = await self._get_or_raise(evolution_id)
        if evo.status != "APPROVED":
            raise ValueError(
                f"Cannot apply evolution {evolution_id}: "
                f"current status is '{evo.status}', expected 'APPROVED'"
            )
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE template_evolutions SET status = 'APPLIED', "
            "applied_at = ?, updated_at = ? WHERE id = ?",
            (now, now, evolution_id),
        )
        self.logger.info(
            "Evolution applied",
            evolution_id=evolution_id,
        )

    # ── Rollback ──────────────────────────────────────────────────

    async def rollback_evolution(self, evolution_id: str) -> None:
        """Roll back an APPLIED evolution, restoring original.

        Transitions status to ROLLED_BACK.
        """
        evo = await self._get_or_raise(evolution_id)
        if evo.status != "APPLIED":
            raise ValueError(
                f"Cannot rollback evolution {evolution_id}: "
                f"current status is '{evo.status}', expected 'APPLIED'"
            )
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE template_evolutions SET status = 'ROLLED_BACK', "
            "updated_at = ? WHERE id = ?",
            (now, evolution_id),
        )
        self.logger.info(
            "Evolution rolled back",
            evolution_id=evolution_id,
        )

    # ── History ───────────────────────────────────────────────────

    async def get_evolution_history(
        self, template_id: str
    ) -> List[TemplateEvolution]:
        """Get all evolution records for a template, newest first."""
        rows = await self.db.fetch_all(
            "SELECT * FROM template_evolutions WHERE template_id = ? "
            "ORDER BY proposed_at DESC",
            (template_id,),
        )
        return [TemplateEvolution.from_dict(dict(r)) for r in rows]

    async def reject_evolution(self, evolution_id: str) -> None:
        """Reject a PROPOSED evolution."""
        evo = await self._get_or_raise(evolution_id)
        if evo.status != "PROPOSED":
            raise ValueError(
                f"Cannot reject evolution {evolution_id}: "
                f"current status is '{evo.status}', expected 'PROPOSED'"
            )
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE template_evolutions SET status = 'REJECTED', "
            "updated_at = ? WHERE id = ?",
            (now, evolution_id),
        )
        self.logger.info(
            "Evolution rejected",
            evolution_id=evolution_id,
        )

    # ── Internal helpers ──────────────────────────────────────────

    async def _get_or_raise(self, evolution_id: str) -> TemplateEvolution:
        row = await self.db.fetch_one(
            "SELECT * FROM template_evolutions WHERE id = ?",
            (evolution_id,),
        )
        if row is None:
            raise ValueError(f"Evolution not found: {evolution_id}")
        return TemplateEvolution.from_dict(dict(row))
