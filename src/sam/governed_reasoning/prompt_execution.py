"""Prompt Execution - WP-05 (MISSION-4.4 / IP-4.4-001).

Menjalankan Prompt melalui jalur Governed Execution. Prompt berjalan melalui
Execution Session, Provider Invocation tervalidasi, Response berhasil
diterima, seluruh execution menghasilkan audit. Approval wajib sebelum
eksekusi (Article V).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .llm_provider import LLMProviderAdapter
from .prompt_model import Prompt
from .prompt_validation import PromptValidator, ValidationResult


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ExecutionSession:
    """Sesi eksekusi prompt (auditable)."""

    session_id: str
    prompt_id: str
    provider_id: str
    status: str = "created"  # created | approved | executing | completed | rejected
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "prompt_id": self.prompt_id,
            "provider_id": self.provider_id,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class PromptResponse:
    """Response hasil eksekusi prompt."""

    session_id: str
    prompt_id: str
    content: str
    provider_id: str
    status: str = "completed"
    metrics: Dict[str, Any] = field(default_factory=dict)
    completed_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "prompt_id": self.prompt_id,
            "content": self.content,
            "provider_id": self.provider_id,
            "status": self.status,
            "metrics": self.metrics,
            "completed_at": self.completed_at,
        }


class PromptExecutor:
    """Eksekutor prompt yang di-govern (approval-gated)."""

    def __init__(
        self, validator: Optional[PromptValidator] = None
    ) -> None:
        self._validator = validator or PromptValidator()
        self._sessions: Dict[str, ExecutionSession] = {}
        self._responses: Dict[str, PromptResponse] = {}

    def create_session(
        self, prompt: Prompt, provider: LLMProviderAdapter
    ) -> ExecutionSession:
        session = ExecutionSession(
            session_id=uuid.uuid4().hex,
            prompt_id=prompt.prompt_id,
            provider_id=provider.metadata.provider_id,
        )
        self._sessions[session.session_id] = session
        return session

    def execute(
        self,
        session: ExecutionSession,
        prompt: Prompt,
        provider: LLMProviderAdapter,
        *,
        approved: bool = False,
    ) -> PromptResponse:
        # Article V: approval wajib sebelum execution
        if not approved:
            raise PermissionError("execution requires approval (Article V)")

        # Prompt harus tervalidasi sebelum eksekusi
        validation: ValidationResult = self._validator.validate(prompt)
        if not validation.valid:
            raise ValueError(
                "prompt validation failed: " + "; ".join(validation.reasons)
            )

        self._sessions[session.session_id] = ExecutionSession(
            session_id=session.session_id,
            prompt_id=session.prompt_id,
            provider_id=session.provider_id,
            status="executing",
        )
        try:
            raw = provider.invoke(
                prompt=prompt.content,
                system=prompt.system,
                session_id=session.session_id,
            )
            content = self._extract_content(provider, raw)
        except Exception as exc:
            self._sessions[session.session_id] = ExecutionSession(
                session_id=session.session_id,
                prompt_id=session.prompt_id,
                provider_id=session.provider_id,
                status="rejected",
            )
            raise RuntimeError(f"provider invocation failed: {exc}") from exc

        response = PromptResponse(
            session_id=session.session_id,
            prompt_id=prompt.prompt_id,
            content=content,
            provider_id=provider.metadata.provider_id,
            metrics={"status": "completed"},
        )
        self._responses[session.session_id] = response
        self._sessions[session.session_id] = ExecutionSession(
            session_id=session.session_id,
            prompt_id=session.prompt_id,
            provider_id=session.provider_id,
            status="completed",
        )
        return response

    @staticmethod
    def _extract_content(provider: LLMProviderAdapter, raw: Any) -> str:
        if isinstance(raw, dict):
            return str(raw.get("content", raw))
        if isinstance(raw, str):
            return raw
        try:
            return raw.content  # type: ignore[attr-defined]
        except Exception:
            return str(raw)

    def get_response(self, session_id: str) -> Optional[PromptResponse]:
        return self._responses.get(session_id)

    def session(self, session_id: str) -> Optional[ExecutionSession]:
        return self._sessions.get(session_id)

    def all_sessions(self) -> Tuple[ExecutionSession, ...]:
        return tuple(self._sessions.values())

    def audit_report(self) -> Dict[str, Any]:
        return {
            "session_count": len(self._sessions),
            "response_count": len(self._responses),
            "sessions": [s.as_dict() for s in self._sessions.values()],
        }
