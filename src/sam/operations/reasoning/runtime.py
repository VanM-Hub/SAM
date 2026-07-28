"""
OP-288 — Conversation Intelligence Runtime

Full pipeline:
  Conversation → PromptBuilder → EvidenceBuilder
  → Gateway → Provider → Normalizer → HallucinationGuard
  → ReasoningResponse

Tidak ada bypass — semua jalur melalui pipeline.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from datetime import datetime

from .provider import ReasoningRequest, ReasoningResponse
from .prompt_builder import PromptBuilder, PromptContext
from .evidence import EvidenceBuilder, EvidenceSet
from .normalizer import ResponseNormalizer
from .guard import HallucinationGuard, GuardResult


@dataclass(frozen=True)
class RuntimeResult:
    response: ReasoningResponse
    context: PromptContext
    evidence: EvidenceSet | None
    guard_result: GuardResult | None
    pipeline_id: str
    duration_ms: float
    success: bool
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "response": self.response.to_dict(),
            "guard": self.guard_result.to_dict() if self.guard_result else None,
        }


class ConversationIntelligenceRuntime:
    """
    Pipeline lengkap untuk Conversation Intelligence.

    Steps:
      1. Build prompt from context
      2. Collect evidence
      3. Select provider via gateway
      4. Generate response
      5. Normalize
      6. Validate with hallucination guard
      7. Return ReasoningResponse
    """

    def __init__(self,
                 prompt_builder: PromptBuilder,
                 evidence_builder: EvidenceBuilder,
                 gateway: Any,
                 normalizer: ResponseNormalizer,
                 guard: HallucinationGuard,
                 ) -> None:
        self._prompt_builder = prompt_builder
        self._evidence_builder = evidence_builder
        self._gateway = gateway
        self._normalizer = normalizer
        self._guard = guard
        self._pipeline_counter = 0

    @property
    def pipeline_count(self) -> int:
        return self._pipeline_counter

    def reason(self,
               operator_question: str,
               conversation_summary: str = "",
               mission_summary: str = "",
               timeline_summary: str = "",
               observation_summary: str = "",
               findings: list[dict[str, Any]] | None = None,
               recommendations: list[dict[str, Any]] | None = None,
               trust_summary: str = "",
               health_summary: str = "",
               provider_name: str = "",
               template_name: str = "",
               system_prompt: str = "",
               temperature: float = 0.0,
               ) -> RuntimeResult:
        """
        Execute full reasoning pipeline.
        """
        import time
        start = time.time()
        self._pipeline_counter += 1
        pid = f"ci-{int(datetime.now().timestamp())}-{self._pipeline_counter}"

        try:
            # 1. Build evidence
            evidence = self._evidence_builder.build(
                observations=[{"detail": observation_summary}] if observation_summary else None,
                findings=findings,
                recommendations=recommendations,
                mission_data={"status": mission_summary} if mission_summary else None,
                timeline_data={"summary": timeline_summary} if timeline_summary else None,
                trust_data={"summary": trust_summary} if trust_summary else None,
                health_data={"summary": health_summary} if health_summary else None,
            )

            # 2. Build prompt context
            context = self._prompt_builder.build(
                operator_question=operator_question,
                conversation_summary=conversation_summary,
                mission_summary=mission_summary,
                timeline_summary=timeline_summary,
                observation_summary=observation_summary,
                findings=findings,
                recommendations=recommendations,
                trust_summary=trust_summary,
                health_summary=health_summary,
                system_prompt=system_prompt,
                template_name=template_name,
                evidence_ids=[e.id for e in evidence.items],
            )

            # 3. Build reasoning request
            request = ReasoningRequest(
                prompt=context.operator_question,
                system_prompt=context.system_prompt,
                temperature=temperature,
                response_format="json" if "json" in template_name else "text",
            )

            # 4. Generate via gateway
            provider = self._gateway.get(provider_name or None)
            raw_response = provider.generate(request)

            # 5. Normalize
            normalized = self._normalizer.normalize(
                raw_response,
                provider=provider.metadata().provider_name if hasattr(provider, 'metadata') else "unknown",
                model=provider.metadata().model_name if hasattr(provider, 'metadata') else "unknown",
            )

            # 6. Hallucination guard
            guard_result = self._guard.validate(
                response=normalized.answer,
                evidence_set=evidence,
                original_confidence=normalized.confidence,
            )

            # 7. Adjust confidence
            adjusted_response = ReasoningResponse(
                answer=normalized.answer,
                citations=normalized.citations,
                confidence=guard_result.adjusted_confidence,
                provider=normalized.provider,
                model=normalized.model,
                usage=normalized.usage,
                latency_ms=normalized.latency_ms,
                warnings=guard_result.warnings,
                unsupported_claims=tuple(
                    v.claim for v in guard_result.claims
                    if v.status != "supported"
                ),
            )

            dur = round((time.time() - start) * 1000, 2)
            return RuntimeResult(
                response=adjusted_response,
                context=context,
                evidence=evidence,
                guard_result=guard_result,
                pipeline_id=pid,
                duration_ms=dur,
                success=True,
            )

        except Exception as e:
            dur = round((time.time() - start) * 1000, 2)
            return RuntimeResult(
                response=ReasoningResponse(answer=f"Error: {e}"),
                context=PromptContext(
                    system_prompt=system_prompt,
                    operator_question=operator_question,
                ),
                evidence=None,
                guard_result=None,
                pipeline_id=pid,
                duration_ms=dur,
                success=False,
                error=str(e),
            )
