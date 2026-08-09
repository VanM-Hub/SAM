"""LLM API - WP-07 (MISSION-4.4 / IP-4.4-001).

Antarmuka standar untuk seluruh capability LLM. API konsisten, dapat
diintegrasikan, mengikuti Governance Flow, dan tidak melakukan bypass
Execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .llm_provider import LLMProviderRegistry
from .llm_credential import CredentialStore
from .prompt_model import Prompt, PromptRepository
from .prompt_execution import PromptExecutor


class Conversation:
    """Sesi percakapan dengan LLM (di-govern)."""

    def __init__(self, conversation_id: str) -> None:
        self.conversation_id = conversation_id
        self._messages: Tuple[Tuple[str, str], ...] = ()

    def add_message(self, role: str, content: str) -> None:
        self._messages += ((role, content),)

    def messages(self) -> Tuple[Tuple[str, str], ...]:
        return self._messages


@dataclass(frozen=True)
class CompletionResult:
    """Hasil completion (read-only)."""

    prompt_id: str
    session_id: str
    content: str
    provider_id: str

    def as_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "session_id": self.session_id,
            "content": self.content,
            "provider_id": self.provider_id,
        }


class PromptAPI:
    """API prompt (read-only koleksi prompt)."""

    def __init__(self, repository: PromptRepository) -> None:
        self._repo = repository

    def get(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        prompt = self._repo.get(prompt_id)
        return prompt.as_dict() if prompt else None

    def all(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(p.as_dict() for p in self._repo.all())


class CompletionAPI:
    """API completion (mengikuti Governance Flow)."""

    def __init__(
        self,
        executor: PromptExecutor,
        repository: PromptRepository,
        registry: LLMProviderRegistry,
    ) -> None:
        self._executor = executor
        self._repo = repository
        self._registry = registry

    def complete(
        self,
        prompt: Prompt,
        *,
        provider_id: str = "",
        approved: bool = False,
    ) -> CompletionResult:
        provider = self._registry.get(provider_id) if provider_id else None
        if provider is None:
            provider = self._pick_provider()
        if provider is None:
            raise ValueError("no LLM provider available")
        session = self._executor.create_session(prompt, provider)
        self._repo.add(prompt)
        response = self._executor.execute(
            session, prompt, provider, approved=approved
        )
        return CompletionResult(
            prompt_id=prompt.prompt_id,
            session_id=session.session_id,
            content=response.content,
            provider_id=provider.metadata.provider_id,
        )

    def _pick_provider(self) -> Any:
        providers = self._registry.list_providers()
        if not providers:
            return None
        return self._registry.get(providers[0])


class LLMAPI:
    """Facade LLM (mengikuti Governance; tidak bypass execution)."""

    def __init__(
        self,
        *,
        registry: LLMProviderRegistry,
        credential: CredentialStore,
        repository: PromptRepository,
        executor: PromptExecutor,
    ) -> None:
        self._registry = registry
        self._credential = credential
        self._repo = repository
        self._executor = executor
        self.prompts = PromptAPI(repository)
        self.completions = CompletionAPI(executor, repository, registry)

    def providers(self) -> Tuple[str, ...]:
        return self._registry.list_providers()

    def provider_status(self, provider_id: str) -> Dict[str, Any]:
        return self._registry.health(provider_id).as_dict()

    def credential_audit(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(e.as_dict() for e in self._credential.audit_report())
