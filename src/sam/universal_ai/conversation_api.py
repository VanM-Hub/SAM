"""Conversation API - WP-28 (MISSION-5.1 / IP-5.1-003).

API publik untuk conversation. Tidak memberikan akses langsung ke provider SDK.
"""
from __future__ import annotations

from typing import Optional, Tuple

from .context_assembly import AssembledContext, ContextAssembler
from .conversation_history import ConversationHistoryStore
from .conversation_model import Conversation
from .conversation_session import ConversationSession, SessionManager
from .message_model import Message, MessageRole
from .provider_invocation import InvocationResult, ProviderInvoker
from .provider_selection import ProviderResolution
from .response_normalization import NormalizedConversationResponse, ResponseNormalizer

import uuid


class ConversationAPI:
    """API publik Conversation Platform."""

    def __init__(
        self,
        invoker: Optional[ProviderInvoker] = None,
        history: Optional[ConversationHistoryStore] = None,
        sessions: Optional[SessionManager] = None,
        normalizer: Optional[ResponseNormalizer] = None,
        assembler: Optional[ContextAssembler] = None,
    ) -> None:
        self.invoker = invoker or ProviderInvoker()
        self.history = history or ConversationHistoryStore()
        self.sessions = sessions or SessionManager()
        self.normalizer = normalizer or ResponseNormalizer()
        self.assembler = assembler or ContextAssembler()

    def create_conversation(self, title: str = "", participant: str = "") -> Conversation:
        convo = Conversation(conversation_id=uuid.uuid4().hex, title=title, participant=participant)
        return convo

    def create_session(self, conversation_id: str, provider_id: str = "", model_id: str = "") -> ConversationSession:
        return self.sessions.create(conversation_id, provider_id=provider_id, model_id=model_id)

    def send_message(
        self,
        *,
        conversation_id: str,
        session_id: str,
        user_message: str,
        resolution: Optional[ProviderResolution] = None,
        provider_id: str = "",
        model_id: str = "",
        context: Optional[AssembledContext] = None,
        evidence_refs: Tuple[str, ...] = (),
    ) -> NormalizedConversationResponse:
        self.history.append(
            Message(
                message_id=uuid.uuid4().hex,
                role=MessageRole.USER,
                content=user_message,
                conversation_id=conversation_id,
                session_id=session_id,
                evidence_refs=evidence_refs,
            )
        )
        eff_provider = provider_id
        eff_model = model_id
        if resolution is not None and resolution.resolved and not eff_provider:
            eff_provider = resolution.selected_provider_id  # type: ignore[assignment]

        ctx = context or self.assembler.assemble(
            history=tuple(m.content for m in self.history.session_history(session_id)),
            user_provided=user_message,
        )
        result = self.invoker.invoke(
            session_id=session_id,
            conversation_id=conversation_id,
            provider_id=eff_provider,
            model_id=eff_model,
            context=ctx,
            resolution=resolution,
        )
        normalized = self.normalizer.normalize(result.response)
        self.history.append(
            Message(
                message_id=uuid.uuid4().hex,
                role=MessageRole.ASSISTANT,
                content=normalized.text,
                conversation_id=conversation_id,
                session_id=session_id,
                evidence_refs=(),
            )
        )
        return normalized

    def resume_session(self, session_id: str) -> Optional[ConversationSession]:
        return self.sessions.resume(session_id)

    def get_history(self, conversation_id: str) -> Tuple[Message, ...]:
        return self.history.history(conversation_id)

    def get_context(self, conversation_id: str) -> AssembledContext:
        return self.assembler.assemble(
            history=tuple(m.content for m in self.history.history(conversation_id))
        )

    def get_response(self, result: InvocationResult) -> NormalizedConversationResponse:
        return self.normalizer.normalize(result.response)

    def close_session(self, session_id: str) -> Optional[ConversationSession]:
        return self.sessions.complete(session_id)
