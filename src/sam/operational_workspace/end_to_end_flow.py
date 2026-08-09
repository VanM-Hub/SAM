"""End-to-End Operations Flow - WP-11..18 (MISSION-4.6 / IP-4.6-002).

Mewujudkan alur operasional end-to-end: Ask SAM -> Investigation ->
Explanation -> Recommendation -> Approval -> Execution -> Verification ->
Learning. Seluruh tahapan menghasilkan evidence, explainable, dan tidak ada
tahapan terputus. Orchestration layer saja (mengonsumsi capability).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class FlowStage:
    ASK = "ask"
    INVESTIGATE = "investigate"
    EXPLAIN = "explain"
    RECOMMEND = "recommend"
    APPROVE = "approve"
    EXECUTE = "execute"
    VERIFY = "verify"
    LEARN = "learn"

    SEQUENCE = (
        ASK, INVESTIGATE, EXPLAIN, RECOMMEND, APPROVE, EXECUTE, VERIFY, LEARN,
    )

    @classmethod
    def index(cls, stage: str) -> int:
        return cls.SEQUENCE.index(stage)


@dataclass(frozen=True)
class FlowEvidence:
    """Evidence dari satu tahapan alur."""

    stage: str
    evidence_id: str
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "stage": self.stage,
            "evidence_id": self.evidence_id,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AskSAMResult:
    """Hasil 'Ask SAM' (masukan operator)."""

    question: str
    intent: str = "investigate"
    context_ref: str = ""

    def as_dict(self) -> dict:
        return {
            "question": self.question,
            "intent": self.intent,
            "context_ref": self.context_ref,
        }


@dataclass(frozen=True)
class FlowStep:
    """Satu langkah dalam alur end-to-end."""

    stage: str
    input: str
    output: Dict[str, Any] = field(default_factory=dict)
    evidence: Tuple[FlowEvidence, ...] = field(default_factory=tuple)
    at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "stage": self.stage,
            "input": self.input,
            "output": self.output,
            "evidence": [e.as_dict() for e in self.evidence],
            "at": self.at,
        }


@dataclass(frozen=True)
class OperationalFlow:
    """Satu siklus operasional end-to-end (atau sampai tahap yang dicapai)."""

    flow_id: str
    question: str
    steps: Tuple[FlowStep, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    @property
    def completed_stages(self) -> Tuple[str, ...]:
        return tuple(s.stage for s in self.steps)

    @property
    def evidence_count(self) -> int:
        return sum(len(s.evidence) for s in self.steps)

    def as_dict(self) -> dict:
        return {
            "flow_id": self.flow_id,
            "question": self.question,
            "steps": [s.as_dict() for s in self.steps],
            "evidence_count": self.evidence_count,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ApprovalContext:
    """Konteks approval untuk tahap eksekusi."""

    pending: bool = True
    approved: bool = False
    approver: str = ""

    def as_dict(self) -> dict:
        return {
            "pending": self.pending,
            "approved": self.approved,
            "approver": self.approver,
        }


class EndToEndFlow:
    """Orkestrator alur end-to-end (mengonsumsi capability via callbacks)."""

    def __init__(
        self,
        *,
        investigate: Callable[[str], Dict[str, Any]],
        explain: Callable[[Dict[str, Any]], Dict[str, Any]],
        recommend: Callable[[Dict[str, Any]], Dict[str, Any]],
        execute: Callable[[Dict[str, Any]], Dict[str, Any]],
        verify: Callable[[Dict[str, Any]], Dict[str, Any]],
        learn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        self._investigate = investigate
        self._explain = explain
        self._recommend = recommend
        self._execute = execute
        self._verify = verify
        self._learn = learn
        self._flows: Dict[str, OperationalFlow] = {}

    def ask(self, question: str, *, intent: str = "investigate") -> str:
        """Tahap 1: Ask SAM. Mengembalikan flow_id; buat alur baru."""
        flow = OperationalFlow(
            flow_id=uuid.uuid4().hex,
            question=question,
            steps=(
                FlowStep(
                    stage=FlowStage.ASK,
                    input=question,
                    output=AskSAMResult(question=question, intent=intent).as_dict(),
                    evidence=(FlowEvidence(FlowStage.ASK, "ask-evid", "question captured"),),
                ),
            ),
        )
        self._flows[flow.flow_id] = flow
        return flow.flow_id

    def run(
        self,
        flow_id: str,
        *,
        require_approval: bool = True,
        approved: bool = False,
    ) -> OperationalFlow:
        """Menjalankan alur penuh dari ASK ke LEARN (approval-gated untuk eksekusi)."""
        flow = self._flows[flow_id]
        steps = list(flow.steps)
        question = flow.question

        inv = self._investigate(question)
        steps.append(self._step(FlowStage.INVESTIGATE, question, inv))

        expl = self._explain(inv)
        steps.append(self._step(FlowStage.EXPLAIN, "explain", expl))

        rec = self._recommend(expl)
        steps.append(self._step(FlowStage.RECOMMEND, "recommend", rec))

        # Approval (Article V) sebelum eksekusi
        approval = ApprovalContext(
            pending=require_approval,
            approved=approved,
            approver="operator" if approved else "",
        )
        if require_approval and not approved:
            # eksekusi diblokir -> alur berhenti (tertunda approval)
            result = OperationalFlow(
                flow_id=flow_id, question=question, steps=tuple(steps)
            )
            self._flows[flow_id] = result
            return result

        # Rekam tahap approval (Article V) sebelum eksekusi
        if require_approval:
            steps.append(
                self._step(FlowStage.APPROVE, "approve", approval.as_dict())
            )

        exec_result = self._execute(rec)
        steps.append(
            self._step(FlowStage.EXECUTE, "execute", exec_result)
        )

        ver = self._verify(exec_result)
        steps.append(self._step(FlowStage.VERIFY, "verify", ver))

        learn_result = self._learn(ver)
        steps.append(self._step(FlowStage.LEARN, "learn", learn_result))

        result = OperationalFlow(
            flow_id=flow_id, question=question, steps=tuple(steps)
        )
        self._flows[flow_id] = result
        return result

    def get(self, flow_id: str) -> OperationalFlow:
        return self._flows[flow_id]

    @staticmethod
    def _step(stage: str, input_text: str, output: Dict[str, Any]) -> FlowStep:
        return FlowStep(
            stage=stage,
            input=input_text,
            output=output,
            evidence=(
                FlowEvidence(stage, f"{stage}-evid", "output captured"),
            ),
        )

    def audit(self) -> Dict[str, Any]:
        return {
            "flow_count": len(self._flows),
            "flows": [f.as_dict() for f in self._flows.values()],
        }
