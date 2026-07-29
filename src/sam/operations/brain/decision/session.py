"""
OP-301 — Decision Session Manager

Mengelola lifecycle sesi keputusan.
Tidak pernah memanggil penyedia eksternal.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import enum


class DecisionState(enum.Enum):
    CREATED = "CREATED"
    COLLECTING = "COLLECTING"
    ANALYZING = "ANALYZING"
    PROPOSING = "PROPOSING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    session_id: str
    operator_question: str
    state: str
    created_at: str
    finished_at: str = ""
    package_summary: str = ""
    evaluation_score: float = 0.0
    alternative_count: int = 0
    selected_alternative: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "session_id": self.session_id,
            "operator_question": self.operator_question,
            "state": self.state,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "package_summary": self.package_summary,
            "evaluation_score": self.evaluation_score,
            "alternative_count": self.alternative_count,
            "selected_alternative": self.selected_alternative,
        }


@dataclass(frozen=True)
class DecisionSnapshot:
    session_id: str
    state: str
    created_at: str
    operator_question: str
    total_decisions: int
    active_decisions_count: int
    latest_state: str
    tokens_used: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "state": self.state,
            "created_at": self.created_at,
            "operator_question": self.operator_question,
            "total_decisions": self.total_decisions,
            "active_decisions_count": self.active_decisions_count,
            "latest_state": self.latest_state,
            "tokens_used": self.tokens_used,
        }


@dataclass
class DecisionHistory:
    records: List[DecisionRecord] = field(default_factory=list)
    max_records: int = 50

    def add(self, record: DecisionRecord) -> None:
        self.records.append(record)
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records:]

    def recent(self, n: int = 10) -> Tuple[DecisionRecord, ...]:
        return tuple(self.records[-n:])

    def by_state(self, state: DecisionState) -> Tuple[DecisionRecord, ...]:
        return tuple(r for r in self.records if r.state == state.value)

    @property
    def count(self) -> int:
        return len(self.records)

    def export(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.records]


class DecisionSession:
    """
    Decision session lifecycle.
    Tidak memanggil penyedia.

    States:
    CREATED → COLLECTING → ANALYZING → PROPOSING → WAITING_APPROVAL → FINISHED
                                                                       → FAILED
    """

    def __init__(self, session_id: str = "", operator_question: str = ""):
        self._session_id = session_id or f"dec-{datetime.now().timestamp():.0f}"
        self._operator_question = operator_question
        self._state = DecisionState.CREATED
        self._created_at = datetime.now().isoformat(timespec="seconds")
        self._history = DecisionHistory()
        self._tokens_used: int = 0
        self._context: Any = None
        self._evaluation: Any = None
        self._alternatives: Tuple[Any, ...] = ()
        self._package: Any = None
        self._approval_request: Any = None

    # ── Properties ────────────────────────────────────────────────

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def operator_question(self) -> str:
        return self._operator_question

    @property
    def state(self) -> DecisionState:
        return self._state

    @property
    def created_at(self) -> str:
        return self._created_at

    @property
    def is_active(self) -> bool:
        return self._state not in (DecisionState.FINISHED, DecisionState.FAILED)

    @property
    def tokens_used(self) -> int:
        return self._tokens_used

    @property
    def history(self) -> DecisionHistory:
        return self._history

    @property
    def decision_count(self) -> int:
        return self._history.count

    # ── State transitions ─────────────────────────────────────────

    def transition(self, target: DecisionState) -> None:
        allowed = self._allowed_transitions()
        if target not in allowed:
            raise ValueError(
                f"Cannot transition from {self._state.value} to {target.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        self._state = target

    def _allowed_transitions(self) -> Tuple[DecisionState, ...]:
        rules = {
            DecisionState.CREATED: (DecisionState.COLLECTING, DecisionState.FAILED),
            DecisionState.COLLECTING: (DecisionState.ANALYZING, DecisionState.FAILED),
            DecisionState.ANALYZING: (DecisionState.PROPOSING, DecisionState.FAILED),
            DecisionState.PROPOSING: (DecisionState.WAITING_APPROVAL, DecisionState.FAILED),
            DecisionState.WAITING_APPROVAL: (DecisionState.FINISHED, DecisionState.FAILED),
            DecisionState.FINISHED: (),
            DecisionState.FAILED: (),
        }
        return rules.get(self._state, ())

    # ── Data setters ──────────────────────────────────────────────

    def set_context(self, context: Any) -> None:
        self._context = context
        if self._state == DecisionState.CREATED:
            self.transition(DecisionState.COLLECTING)

    def set_evaluation(self, evaluation: Any) -> None:
        self._evaluation = evaluation
        if self._state == DecisionState.COLLECTING:
            self.transition(DecisionState.ANALYZING)

    def set_alternatives(self, alternatives: Tuple[Any, ...]) -> None:
        self._alternatives = alternatives
        if self._state == DecisionState.ANALYZING:
            self.transition(DecisionState.PROPOSING)

    def set_package(self, package: Any) -> None:
        self._package = package
        if self._state == DecisionState.PROPOSING:
            self.transition(DecisionState.WAITING_APPROVAL)

    def set_approval_request(self, request: Any) -> None:
        self._approval_request = request

    def finish(self, summary: str = "") -> None:
        if self._state not in (DecisionState.FAILED, DecisionState.FINISHED):
            self.transition(DecisionState.FINISHED)
        record = DecisionRecord(
            decision_id=f"{self._session_id}-{self._history.count + 1}",
            session_id=self._session_id,
            operator_question=self._operator_question,
            state=self._state.value,
            created_at=self._created_at,
            finished_at=datetime.now().isoformat(timespec="seconds"),
            package_summary=summary,
            evaluation_score=self._evaluation.score if self._evaluation else 0.0,
            alternative_count=len(self._alternatives),
            selected_alternative=self._get_selected(),
        )
        self._history.add(record)

    def fail(self, reason: str = "") -> None:
        self._state = DecisionState.FAILED
        record = DecisionRecord(
            decision_id=f"{self._session_id}-{self._history.count + 1}",
            session_id=self._session_id,
            operator_question=self._operator_question,
            state=DecisionState.FAILED.value,
            created_at=self._created_at,
            finished_at=datetime.now().isoformat(timespec="seconds"),
            package_summary=reason,
        )
        self._history.add(record)

    def _get_selected(self) -> str:
        if self._package and hasattr(self._package, "selected_alternative"):
            return self._package.selected_alternative
        return ""

    # ── Snapshot ──────────────────────────────────────────────────

    def snapshot(self) -> DecisionSnapshot:
        return DecisionSnapshot(
            session_id=self._session_id,
            state=self._state.value,
            created_at=self._created_at,
            operator_question=self._operator_question,
            total_decisions=self._history.count,
            active_decisions_count=1 if self.is_active else 0,
            latest_state=self._state.value,
            tokens_used=self._tokens_used,
        )

    # ── Token tracking ────────────────────────────────────────────

    def add_tokens(self, count: int) -> None:
        self._tokens_used += count
