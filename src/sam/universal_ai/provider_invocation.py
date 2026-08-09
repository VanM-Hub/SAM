"""Provider Invocation - WP-25 (MISSION-5.1 / IP-5.1-003).

Menghubungkan Conversation Platform dengan Provider Adapter. Invocation melalui
execution boundary; tidak ada direct vendor invocation dari conversation domain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from .adapter_framework import NormalizedResponse, ProviderAdapter, ProviderAdapterError
from .context_assembly import AssembledContext
from .provider_selection import ProviderResolution


@dataclass(frozen=True)
class InvocationResult:
    """Hasil invokasi provider."""

    session_id: str
    conversation_id: str
    provider_id: str
    model_id: str
    response: NormalizedResponse
    timed_out: bool = False
    error: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "response": self.response.as_dict(),
            "timed_out": self.timed_out,
            "error": self.error,
        }


class ProviderInvoker:
    """Meneruskan request ke adapter melalui abstraction (bukan SDK langsung)."""

    def __init__(
        self,
        adapters: Tuple[ProviderAdapter, ...] = (),
        timeout_fn: Optional[Callable[[str], bool]] = None,
    ) -> None:
        self._adapters = {a.provider_id: a for a in adapters}
        self._timeout_fn = timeout_fn or (lambda _pid: False)

    def register(self, adapter: ProviderAdapter) -> None:
        self._adapters[adapter.provider_id] = adapter

    def invoke(
        self,
        *,
        session_id: str,
        conversation_id: str,
        provider_id: str,
        model_id: str,
        context: AssembledContext,
        resolution: Optional[ProviderResolution] = None,
        prompt: str = "",
    ) -> InvocationResult:
        effective_provider = provider_id
        if (not effective_provider or effective_provider not in self._adapters) and resolution is not None and resolution.resolved:
            effective_provider = resolution.selected_provider_id  # type: ignore[assignment]

        timed_out = self._timeout_fn(effective_provider or "")
        if timed_out:
            return InvocationResult(
                session_id=session_id,
                conversation_id=conversation_id,
                provider_id=effective_provider or "",
                model_id=model_id,
                response=self._empty_response(effective_provider or "", model_id),
                timed_out=True,
                error="timeout",
            )

        adapter = self._adapters.get(effective_provider)
        if adapter is None:
            raise ProviderAdapterError(effective_provider or "unknown", "no_adapter", "no adapter for provider")

        text = context.assembled_text if context.assembled_text else prompt

        from .adapter_framework import ProviderRequest

        request = ProviderRequest(provider_id=effective_provider, prompt=text, model_id=model_id)

        try:
            response = adapter.invoke(request)
        except ProviderAdapterError as exc:
            return InvocationResult(
                session_id=session_id,
                conversation_id=conversation_id,
                provider_id=effective_provider,
                model_id=model_id,
                response=self._empty_response(effective_provider, model_id),
                error=exc.code,
            )
        return InvocationResult(
            session_id=session_id,
            conversation_id=conversation_id,
            provider_id=effective_provider,
            model_id=response.model_id or model_id,
            response=response,
        )

    @staticmethod
    def _empty_response(provider_id: str, model_id: str) -> NormalizedResponse:
        return NormalizedResponse(text="", provider_id=provider_id, model_id=model_id, error="empty")
