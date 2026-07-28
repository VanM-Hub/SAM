"""
OP-285 — Response Normalizer

Semua provider response dikonversi menjadi ReasoningResponse seragam.
Provider-specific data tidak bocor keluar.
"""

from __future__ import annotations
from typing import Any

from .provider import ReasoningResponse, UsageMetrics


class ResponseNormalizer:
    """
    Menormalkan response dari berbagai provider ke ReasoningResponse seragam.

    Konversi:
      - Provider raw → ReasoningResponse
      - Semua field optional diisi default
      - Provider-specific fields tidak bocor
    """

    def normalize(self, raw: Any,
                  provider: str = "unknown",
                  model: str = "unknown") -> ReasoningResponse:
        """
        Normalize raw provider output ke ReasoningResponse seragam.
        """
        if isinstance(raw, ReasoningResponse):
            return raw

        if isinstance(raw, dict):
            return self._from_dict(raw, provider, model)

        if isinstance(raw, str):
            return ReasoningResponse(
                answer=raw,
                provider=provider,
                model=model,
            )

        # Fallback
        return ReasoningResponse(
            answer=str(raw) if raw else "",
            provider=provider,
            model=model,
        )

    def _from_dict(self, raw: dict[str, Any],
                   provider: str, model: str) -> ReasoningResponse:
        return ReasoningResponse(
            answer=raw.get("answer") or raw.get("text") or "",
            citations=tuple(
                raw.get("citations") or raw.get("references") or []),
            confidence=raw.get("confidence", 1.0),
            provider=raw.get("provider", provider),
            model=raw.get("model", model),
            usage=UsageMetrics(
                prompt_tokens=raw.get("prompt_tokens", 0),
                completion_tokens=raw.get("completion_tokens", 0),
                total_tokens=raw.get("total_tokens", 0),
                cost_usd=raw.get("cost_usd", 0.0),
            ),
            latency_ms=raw.get("latency_ms", 0.0),
            warnings=tuple(raw.get("warnings") or raw.get("alerts") or []),
            unsupported_claims=(),
            raw_response=str(raw).strip(),
        )

    def safe_wrap(self, response: ReasoningResponse) -> ReasoningResponse:
        """
        Ensure no extra fields leak from provider-specific data.
        Only standard ReasoningResponse fields survive.
        """
        return ReasoningResponse(
            answer=response.answer,
            citations=response.citations,
            confidence=min(max(response.confidence, 0.0), 1.0),
            provider=response.provider,
            model=response.model,
            usage=UsageMetrics(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cost_usd=response.usage.cost_usd,
            ),
            latency_ms=response.latency_ms,
            warnings=response.warnings,
            unsupported_claims=response.unsupported_claims,
            raw_response=response.raw_response,
        )

    def merge(self, responses: list[ReasoningResponse]) -> ReasoningResponse:
        """Merge multiple responses (e.g. from multiple providers)."""
        if not responses:
            return ReasoningResponse(answer="")

        if len(responses) == 1:
            return responses[0]

        combined_answer = "\n\n---\n\n".join(r.answer for r in responses
                                              if r.answer)
        all_citations: list[tuple[str, float]] = []
        all_warnings: list[str] = []
        all_unsupported: list[str] = []
        total_latency = 0.0
        total_usage = UsageMetrics()

        for r in responses:
            all_citations.extend(r.citations)
            all_warnings.extend(r.warnings)
            all_unsupported.extend(r.unsupported_claims)
            total_latency += r.latency_ms
            total_usage = UsageMetrics(
                prompt_tokens=total_usage.prompt_tokens + r.usage.prompt_tokens,
                completion_tokens=total_usage.completion_tokens + r.usage.completion_tokens,
                total_tokens=total_usage.total_tokens + r.usage.total_tokens,
                cost_usd=total_usage.cost_usd + r.usage.cost_usd,
            )

        avg_confidence = sum(r.confidence for r in responses) / len(responses)

        return ReasoningResponse(
            answer=combined_answer,
            citations=tuple(all_citations),
            confidence=round(avg_confidence, 2),
            provider=",".join(r.provider for r in responses),
            model=",".join(r.model for r in responses),
            usage=total_usage,
            latency_ms=round(total_latency, 2),
            warnings=tuple(all_warnings),
            unsupported_claims=tuple(all_unsupported),
        )
