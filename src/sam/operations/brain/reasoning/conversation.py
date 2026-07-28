"""
OP-297 — Conversation Integration

DTO query untuk conversation integration.
Conversation tetap menjadi satu-satunya pintu masuk.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from sam.operations.reasoning.provider import ReasoningResponse


# ── DTO Query ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class AskOperationalQuestion:
    question: str
    context_summary: str = ""
    evidence_ids: Tuple[str, ...] = ()
    template: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "context_summary": self.context_summary,
            "evidence_ids": list(self.evidence_ids),
            "template": self.template,
        }


@dataclass(frozen=True)
class AskMissionQuestion:
    question: str
    mission_id: str = ""
    mission_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "mission_id": self.mission_id,
            "mission_summary": self.mission_summary,
        }


@dataclass(frozen=True)
class AskHealthQuestion:
    question: str
    health_summary: str = ""
    component_filter: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "health_summary": self.health_summary,
            "component_filter": list(self.component_filter),
        }


@dataclass(frozen=True)
class AskEvidenceQuestion:
    question: str
    evidence_ids: Tuple[str, ...] = ()
    observation_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "evidence_ids": list(self.evidence_ids),
            "observation_summary": self.observation_summary,
        }


@dataclass(frozen=True)
class AskRecommendationQuestion:
    question: str
    findings_summary: str = ""
    options: Tuple[str, ...] = ()
    risk_threshold: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "findings_summary": self.findings_summary,
            "options": list(self.options),
            "risk_threshold": self.risk_threshold,
        }


# ── Integration ────────────────────────────────────────────────────

@dataclass(frozen=True)
class ReasoningResult:
    response: ReasoningResponse
    session_id: str
    validation_passed: bool
    pipeline_duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response.to_dict(),
            "session_id": self.session_id,
            "validation_passed": self.validation_passed,
            "pipeline_duration_ms": self.pipeline_duration_ms,
        }


class ConversationReasoningIntegration:
    """
    Jembatan antara Conversation dan Reasoning Pipeline.
    Conversation tetap menjadi satu-satunya pintu masuk.

    Semua query dikonversi ke pipeline call.
    """
    def __init__(self, pipeline: Any):
        self._pipeline = pipeline

    def ask_operational(self, query: AskOperationalQuestion) -> ReasoningResult:
        result = self._pipeline.run(
            operator_question=query.question,
            system_prompt=query.context_summary,
        )
        return self._wrap(result)

    def ask_mission(self, query: AskMissionQuestion) -> ReasoningResult:
        result = self._pipeline.run(
            operator_question=query.question,
        )
        return self._wrap(result)

    def ask_health(self, query: AskHealthQuestion) -> ReasoningResult:
        result = self._pipeline.run(
            operator_question=query.question,
        )
        return self._wrap(result)

    def ask_evidence(self, query: AskEvidenceQuestion) -> ReasoningResult:
        result = self._pipeline.run(
            operator_question=query.question,
        )
        return self._wrap(result)

    def ask_recommendation(self, query: AskRecommendationQuestion) -> ReasoningResult:
        result = self._pipeline.run(
            operator_question=query.question,
        )
        return self._wrap(result)

    def _wrap(self, pipeline_result: Any) -> ReasoningResult:
        # Build ReasoningResponse dari PipelineResult
        from sam.operations.reasoning.provider import (ReasoningResponse, UsageMetrics)
        response = ReasoningResponse(
            answer=pipeline_result.answer,
            confidence=pipeline_result.confidence,
            provider=pipeline_result.provider_name,
            usage=UsageMetrics(),
            latency_ms=pipeline_result.latency_ms,
            warnings=tuple(
                i.message for i in pipeline_result.validation.issues
                if i.severity == "warning"
            ),
        )
        return ReasoningResult(
            response=response,
            session_id=pipeline_result.session_id,
            validation_passed=pipeline_result.validation.passed,
            pipeline_duration_ms=pipeline_result.latency_ms,
        )
