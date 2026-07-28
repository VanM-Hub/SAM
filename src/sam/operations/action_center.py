"""
ActionCenterDTO — Pure DTO for action center information.

No renderer, no logic. Plain data transport object ready for CLI, GUI, or conversation.
All fields are optional so partial data is never an error.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ActionCenterItem:
    """Single actionable item visible to the user."""
    id: str
    kind: str  # "approval" | "mission" | "verification" | "recovery" | "alert"
    title: str
    description: str = ""
    status: str = "pending"  # "pending" | "approved" | "rejected" | "running" | "failed" | "completed"
    risk: str = "normal"  # "low" | "normal" | "high" | "critical"
    created_at: str = ""
    updated_at: str = ""
    priority: int = 0  # Higher = more urgent


@dataclass
class ActionCenterDTO:
    """Complete action center snapshot — ready for any frontend.

    All lists are sorted by priority descending.
    """

    # ── Core buckets ──────────────────────────────────────────────────
    pending_approvals: list[ActionCenterItem] = field(default_factory=list)
    pending_missions: list[ActionCenterItem] = field(default_factory=list)
    failed_missions: list[ActionCenterItem] = field(default_factory=list)
    waiting_verification: list[ActionCenterItem] = field(default_factory=list)
    waiting_human: list[ActionCenterItem] = field(default_factory=list)

    # ── Risk buckets ──────────────────────────────────────────────────
    high_risk: list[ActionCenterItem] = field(default_factory=list)
    critical_risk: list[ActionCenterItem] = field(default_factory=list)

    # ── History ───────────────────────────────────────────────────────
    recent_decisions: list[ActionCenterItem] = field(default_factory=list)

    # ── Metadata ──────────────────────────────────────────────────────
    total_pending: int = 0
    total_failed: int = 0
    total_high_risk: int = 0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # ── Convenience ───────────────────────────────────────────────────

    @property
    def has_action_items(self) -> bool:
        return self.total_pending > 0 or self.total_failed > 0 or self.total_high_risk > 0

    @property
    def summary(self) -> str:
        parts = []
        if self.total_pending:
            parts.append(f"{self.total_pending} pending")
        if self.total_failed:
            parts.append(f"{self.total_failed} failed")
        if self.total_high_risk:
            parts.append(f"{self.total_high_risk} high-risk")
        return " | ".join(parts) if parts else "Everything clear"


# ── Builder ───────────────────────────────────────────────────────────

class ActionCenterBuilder:
    """Populates an ActionCenterDTO from operational repositories."""

    def __init__(self) -> None:
        pass

    def build(self) -> ActionCenterDTO:
        """Build the full DTO from live data sources.

        Returns a complete DTO even if all lists are empty.
        """
        dto = ActionCenterDTO()

        # Each _populate_* method reads from its respective source
        # and appends items to the appropriate list.
        self._populate_approvals(dto)
        self._populate_missions(dto)
        self._populate_verifications(dto)
        self._populate_decisions(dto)
        self._populate_risk(dto)

        # Aggregate totals
        dto.total_pending = (
            len(dto.pending_approvals)
            + len(dto.pending_missions)
            + len(dto.waiting_verification)
            + len(dto.waiting_human)
        )
        dto.total_failed = len(dto.failed_missions)
        dto.total_high_risk = len(dto.high_risk) + len(dto.critical_risk)

        return dto

    # ── Population stubs ──────────────────────────────────────────────
    # Each reads from its repository through the existing domain layer.

    def _populate_approvals(self, dto: ActionCenterDTO) -> None:
        """Read approval repository for pending/expired approvals."""
        # Stub — real implementation delegates to approval_repo
        pass

    def _populate_missions(self, dto: ActionCenterDTO) -> None:
        """Read mission repository for pending/running/failed missions."""
        # Stub — real implementation delegates to mission_repo
        pass

    def _populate_verifications(self, dto: ActionCenterDTO) -> None:
        """Read verification state from execution / audit repositories."""
        # Stub — real implementation delegates to execution or audit repo
        pass

    def _populate_decisions(self, dto: ActionCenterDTO) -> None:
        """Read recent decisions from decision history repository."""
        # Stub — real implementation delegates to decision_repo
        pass

    def _populate_risk(self, dto: ActionCenterDTO) -> None:
        """Classify existing items into high / critical risk buckets."""
        # Stub — real implementation cross-references risk classifiers
        pass
