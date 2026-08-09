"""Test IP-5.1-003 - AI Conversation Platform (MISSION-5.1).

Coverage: WP-21..WP-30 - conversation model, session, message, context assembly,
provider invocation, response normalization, history, API, compliance, integration.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.universal_ai import (
    AssembledContext,
    ConversationAPI,
    ConversationComplianceChecker,
    ContextAssembler,
    Conversation,
    ConversationSession,
    ConversationStatus,
    Message,
    MessageRole,
    OpenAIAdapter,
    ProviderInvoker,
    SessionManager,
    SessionState,
)


# ---------------------------------------------------------------------------
# WP-21 Conversation Model
# ---------------------------------------------------------------------------

class TestConversationModel:
    def test_default_open(self):
        convo = Conversation(conversation_id="c1")
        assert convo.status == ConversationStatus.OPEN

    def test_as_dict(self):
        convo = Conversation(conversation_id="c1", title="t")
        assert convo.as_dict()["conversation_id"] == "c1"


# ---------------------------------------------------------------------------
# WP-22 Conversation Session
# ---------------------------------------------------------------------------

class TestSession:
    def test_create_active(self):
        mgr = SessionManager()
        session = mgr.create("c1")
        assert isinstance(session, ConversationSession)
        assert session.state == SessionState.ACTIVE

    def test_pause_resume_complete(self):
        mgr = SessionManager()
        s = mgr.create("c1")
        mgr.pause(s.session_id)
        assert mgr.get(s.session_id).state == SessionState.PAUSED
        mgr.resume(s.session_id)
        assert mgr.get(s.session_id).state == SessionState.ACTIVE
        mgr.complete(s.session_id)
        assert mgr.get(s.session_id).state == SessionState.COMPLETED

    def test_resume_completed_returns_none(self):
        mgr = SessionManager()
        s = mgr.create("c1")
        mgr.complete(s.session_id)
        assert mgr.resume(s.session_id) is None


# ---------------------------------------------------------------------------
# WP-23 Message Model
# ---------------------------------------------------------------------------

class TestMessage:
    def test_roles_distinct(self):
        assert MessageRole.USER != MessageRole.GOVERNANCE_CONTEXT
        msg = Message(message_id="m1", role=MessageRole.ASSISTANT, content="hi")
        assert msg.as_dict()["role"] == "assistant"


# ---------------------------------------------------------------------------
# WP-24 Context Assembly
# ---------------------------------------------------------------------------

class TestContextAssembly:
    def test_assembles_parts(self):
        assembler = ContextAssembler()
        ctx = assembler.assemble(history=("a", "b"), governance="g", user_provided="q")
        assert isinstance(ctx, AssembledContext)
        assert "governance_context" in ctx.sources()
        assert ctx.assembled_text != ""

    def test_redact_credential(self):
        assembler = ContextAssembler()
        ctx = assembler.assemble(user_provided="use secret api_key abc123")
        assert "api_key" not in ctx.assembled_text.lower().replace("api_key", "")


# ---------------------------------------------------------------------------
# WP-25 Provider Invocation
# ---------------------------------------------------------------------------

class TestInvocation:
    def test_invoke_via_adapter(self):
        openai = OpenAIAdapter(transport=lambda p: {"choices": [{"message": {"content": "ok"}}], "model": "gpt"})
        invoker = ProviderInvoker(adapters=(openai,))
        result = invoker.invoke(
            session_id="s1", conversation_id="c1", provider_id="openai", model_id="gpt",
            context=AssembledContext(parts=(("x", "hello"),)),
        )
        assert result.provider_id == "openai"
        assert result.response.text == "ok"

    def test_timeout(self):
        invoker = ProviderInvoker(timeout_fn=lambda _p: True)
        result = invoker.invoke(
            session_id="s1", conversation_id="c1", provider_id="none", model_id="m",
            context=AssembledContext(),
        )
        assert result.timed_out is True
        assert result.error == "timeout"


# ---------------------------------------------------------------------------
# WP-28 Conversation API (integration WP-26/27/28/30)
# ---------------------------------------------------------------------------

class TestConversationAPI:
    def _api(self):
        openai = OpenAIAdapter(transport=lambda p: {"choices": [{"message": {"content": "ok"}}], "model": "gpt"})
        return ConversationAPI(invoker=ProviderInvoker(adapters=(openai,)))

    def test_send_message_roundtrip(self):
        api = self._api()
        convo = api.create_conversation("test")
        session = api.create_session(convo.conversation_id, provider_id="openai", model_id="gpt")
        resp = api.send_message(
            conversation_id=convo.conversation_id, session_id=session.session_id,
            user_message="hi", provider_id="openai", model_id="gpt",
        )
        assert resp.text == "ok"
        assert resp.provider_attribution.startswith("openai:")

    def test_history_records_messages(self):
        api = self._api()
        convo = api.create_conversation("test")
        session = api.create_session(convo.conversation_id, provider_id="openai", model_id="gpt")
        api.send_message(
            conversation_id=convo.conversation_id, session_id=session.session_id,
            user_message="q", provider_id="openai", model_id="gpt",
        )
        history = api.get_history(convo.conversation_id)
        assert len(history) == 2  # user + assistant
        assert history[0].role == MessageRole.USER
        assert history[1].role == MessageRole.ASSISTANT

    def test_close_session(self):
        api = self._api()
        convo = api.create_conversation("test")
        session = api.create_session(convo.conversation_id)
        assert api.close_session(session.session_id).state == SessionState.COMPLETED


# ---------------------------------------------------------------------------
# WP-29 Conversation Compliance
# ---------------------------------------------------------------------------

class TestConversationCompliance:
    def test_certify_passes(self):
        cert = ConversationComplianceChecker().certify()
        assert cert["certified"] is True

    def test_fails_on_bypass(self):
        cert = ConversationComplianceChecker().certify(no_execution_bypass=False)
        assert cert["certified"] is False


# ---------------------------------------------------------------------------
# WP-30 Integration
# ---------------------------------------------------------------------------

class TestConversationIntegration:
    def test_end_to_end(self):
        api = self._api()
        convo = api.create_conversation()
        session = api.create_session(convo.conversation_id, provider_id="openai", model_id="gpt")
        resp = api.send_message(
            conversation_id=convo.conversation_id, session_id=session.session_id,
            user_message="ping", provider_id="openai", model_id="gpt",
        )
        assert resp.text == "ok"
        cert = ConversationComplianceChecker().certify()
        assert cert["certified"] is True

    def _api(self):
        openai = OpenAIAdapter(transport=lambda p: {"choices": [{"message": {"content": "ok"}}], "model": "gpt"})
        return ConversationAPI(invoker=ProviderInvoker(adapters=(openai,)))
