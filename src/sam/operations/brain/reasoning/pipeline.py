"""
OP-296 — Reasoning Pipeline

Pipeline lengkap:
  Context → Strategy → PromptBuilder → Provider → Normalizer → EvidenceGuard → Validator → ReasoningResponse

Fully synchronous. Tidak ada async.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import time

from .session import ReasoningSession, ReasoningContext
from .context_builder import ContextAssembler, ObservationSnapshot, MissionDashboardDTO, TimelineSummary, MissionSummary
from .strategy import StrategyEngine, ReasoningMode, PromptStrategy
from .scheduler import ProviderScheduler
from .validator import ResponseValidator, ValidationReport
from .. import reasoning as _r


@dataclass(frozen=True)
class PipelineResult:
    answer: str
    confidence: float
    session_id: str
    mode: str
    template_name: str
    provider_name: str
    latency_ms: float
    attempts: int
    validation: ValidationReport
    token_estimate: int
    evidence_ids: Tuple[str, ...]
    timestamps: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer[:200],
            "confidence": self.confidence,
            "session_id": self.session_id,
            "mode": self.mode,
            "template_name": self.template_name,
            "provider_name": self.provider_name,
            "latency_ms": self.latency_ms,
            "attempts": self.attempts,
            "validation": self.validation.to_dict(),
            "token_estimate": self.token_estimate,
            "evidence_ids": list(self.evidence_ids),
        }


class ReasoningPipeline:
    """
    Pipeline synchronous reasoning.

    Steps:
    1. Resolve strategy (Context → Strategy)
    2. Build prompt via ContextAssembler
    3. Set session context
    4. Schedule & generate via ProviderScheduler
    5. Validate via ResponseValidator
    6. Record in session history
    7. Return PipelineResult
    """

    def __init__(self,
                 session: ReasoningSession,
                 context_assembler: ContextAssembler,
                 strategy_engine: StrategyEngine,
                 scheduler: ProviderScheduler,
                 validator: ResponseValidator,
                 ):
        self._session = session
        self._context_assembler = context_assembler
        self._strategy_engine = strategy_engine
        self._scheduler = scheduler
        self._validator = validator
        self._timestamps: Dict[str, str] = {}

    @property
    def session(self) -> ReasoningSession:
        return self._session

    def run(self, operator_question: str,
            mode: Optional[ReasoningMode] = None,
            preferred_provider: str = "",
            observations: Optional[ObservationSnapshot] = None,
            mission_dashboard: Optional[MissionDashboardDTO] = None,
            timeline: Optional[TimelineSummary] = None,
            mission: Optional[MissionSummary] = None,
            system_prompt: str = "",
            ) -> PipelineResult:
        """
        Jalankan pipeline reasoning lengkap.
        """
        self._timestamps = {"start": datetime.now().isoformat(timespec="seconds")}
        start = time.time()

        # 1. Resolve strategy
        if mode is None:
            mode = self._strategy_engine.resolve_mode(operator_question)
        strategy = self._strategy_engine.get_strategy(mode)
        self._timestamps["strategy"] = datetime.now().isoformat(timespec="seconds")

        # 2. Build context
        context = self._context_assembler.assemble(
            operator_question=operator_question,
            observations=observations,
            mission_dashboard=mission_dashboard,
            timeline=timeline,
            mission=mission,
            template_name=strategy.template_name,
            system_prompt=system_prompt,
        )
        self._timestamps["context"] = datetime.now().isoformat(timespec="seconds")

        # 3. Set session context
        self._session.set_context(context)
        self._timestamps["session"] = datetime.now().isoformat(timespec="seconds")

        # 4. Build prompt & schedule
        # Use sam.operations.reasoning provider protocol via scheduler
        request = self._build_request(context, strategy)
        scheduler_result = self._scheduler.schedule(request, preferred=preferred_provider)
        self._timestamps["generation"] = datetime.now().isoformat(timespec="seconds")

        # Extract response
        if scheduler_result.success and scheduler_result.response:
            from sam.operations.reasoning.provider import ReasoningResponse
            if isinstance(scheduler_result.response, ReasoningResponse):
                answer = scheduler_result.response.answer
                confidence = scheduler_result.response.confidence
                citations = scheduler_result.response.citations
                unsupported_claims = scheduler_result.response.unsupported_claims
                total_claims = len(scheduler_result.response.citations) + 1
                supported_claims = total_claims - len(unsupported_claims)
            elif isinstance(scheduler_result.response, dict):
                answer = scheduler_result.response.get("answer", "")
                confidence = scheduler_result.response.get("confidence", 1.0)
                citations = scheduler_result.response.get("citations", ())
                unsupported_claims = scheduler_result.response.get("unsupported_claims", ())
                total_claims = 1
                supported_claims = total_claims - len(unsupported_claims)
            else:
                answer = str(scheduler_result.response)
                confidence = 1.0
                citations = ()
                unsupported_claims = ()
                total_claims = 1
                supported_claims = 1
        else:
            answer = f"Provider unavailable: {scheduler_result.error}"
            confidence = 0.0
            citations = ()
            unsupported_claims = ("Provider unavailable",)
            total_claims = 1
            supported_claims = 0

        # 5. Validate
        validation = self._validator.validate(
            answer=answer,
            confidence=confidence,
            evidence_ids=context.evidence_ids,
            citations=citations,
            unsupported_claims=unsupported_claims,
            supported_claims=supported_claims,
            total_claims=total_claims,
            required_evidence=strategy.requires_evidence,
        )
        self._timestamps["validation"] = datetime.now().isoformat(timespec="seconds")

        # 6. Record in session
        self._session.record_reasoning(
            question=operator_question,
            template_name=strategy.template_name,
            token_estimate=context.token_estimate,
            response_preview=answer[:200],
            confidence=confidence,
        )

        duration = round((time.time() - start) * 1000, 2)

        return PipelineResult(
            answer=answer,
            confidence=confidence,
            session_id=self._session.session_id,
            mode=mode.value,
            template_name=strategy.template_name,
            provider_name=scheduler_result.provider_name,
            latency_ms=duration,
            attempts=scheduler_result.attempts,
            validation=validation,
            token_estimate=context.token_estimate,
            evidence_ids=context.evidence_ids,
            timestamps=self._timestamps,
        )

    def _build_request(self, context: ReasoningContext,
                       strategy: PromptStrategy) -> Any:
        """Build request object untuk provider protocol."""
        from sam.operations.reasoning.provider import ReasoningRequest
        return ReasoningRequest(
            prompt=context.operator_question,
            system_prompt=context.system_prompt or strategy.description,
            temperature=0.0,
            max_tokens=2000,
            response_format="json" if "compare" in strategy.template_name else "text",
        )

    def run_mode(self, operator_question: str,
                 mode: ReasoningMode,
                 **kwargs: Any) -> PipelineResult:
        """Jalankan pipeline dengan mode eksplisit."""
        return self.run(operator_question=operator_question, mode=mode, **kwargs)
