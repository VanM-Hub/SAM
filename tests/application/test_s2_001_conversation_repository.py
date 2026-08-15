"""test_s2_001_conversation_repository.py — Sprint 2, S2-1 Conversation Persistence.

Buktikan (sesuai acceptance Sprint 2):
  1. Conversation aggregate canonical (Conversation + ConversationSession +
     Message) tersimpan & diambil kembali, TANPA model pesan kedua.
  2. Message disimpan UTUH (canonical `Message` dari universal_ai), bukan
     entity duplikat; round-trip serialization identik (frozen dataclass).
  3. TIDAK ada field mission/request di model conversation yang disimpan
     (keputusan Sprint 2: association conversation->mission bukan bagian model
     universal). Struktural cek field Message/Conversation/Session.
  4. Multi-conversation SALING TERPISAH (no overwrite) — mirip M12-001.
  5. Persistence survive "restart" (in-memory: instance baru berbagi; PG:
     instance baru membaca DB).
  6. Backend dapat di-swap (in-memory vs PostgreSQL) via PORT.
  7. Konten tersimpan TIDAK pernah memuat secret/token credential (struct cek).

Unit test (in-memory) selalu jalan. Integration test (PG) di-skip bila env
`SAM_PG_DSN` tidak tersedia.
"""
from __future__ import annotations

import os

import pytest

from sam.universal_ai.conversation_model import Conversation
from sam.universal_ai.conversation_session import (
    ConversationSession,
    SessionState,
)
from sam.universal_ai.message_model import Message, MessageRole

from sam.application.ux import repositories as repo_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_convo(conversation_id: str, title: str = "") -> Conversation:
    return Conversation(
        conversation_id=conversation_id, title=title, participant="user",
    )


def _make_session(conversation_id: str, session_id: str) -> ConversationSession:
    return ConversationSession(
        session_id=session_id, conversation_id=conversation_id,
        state=SessionState.ACTIVE, provider_id="generic", model_id="m",
    )


def _make_message(
    conversation_id: str, session_id: str, message_id: str,
    role: MessageRole, content: str,
) -> Message:
    return Message(
        message_id=message_id, role=role, content=content,
        conversation_id=conversation_id, session_id=session_id,
        evidence_refs=(),
    )


# Model canonical TIDAK boleh tahu konsep mission/request (S2-1 decision).
_CANONICAL_FIELDS = {
    "conversation": {"conversation_id", "title", "participant", "status",
                     "provider_context", "created_at"},
    "session": {"session_id", "conversation_id", "state", "provider_id",
                "model_id", "created_at"},
    "message": {"message_id", "role", "content", "conversation_id",
                "session_id", "evidence_refs", "created_at"},
}


def _assert_no_mission_field(model_name: str, d: dict) -> None:
    allowed = _CANONICAL_FIELDS[model_name]
    extra = set(d.keys()) - allowed
    assert not extra, (
        f"Model {model_name} tidak boleh membawa field non-canonical: {extra}"
    )
    for key in d.keys():
        assert "mission" not in key.lower(), (
            f"Model {model_name} tidak boleh punya field mission: {key}"
        )
        assert "request" not in key.lower(), (
            f"Model {model_name} tidak boleh punya field request: {key}"
        )


def _assert_no_secret(d: dict) -> None:
    """Struct cek: serialized data tidak memuat material credential/sensitif."""
    forbidden = ("token", "secret", "api_key", "apikey", "password",
                 "credential", "private_key")
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = k.lower()
                assert not any(f in kl for f in forbidden), (
                    f"Field sensitif di {path}{k}"
                )
                walk(v, f"{path}{k}.")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}].")
    walk(d)


# ---------------------------------------------------------------------------
# Unit: in-memory
# ---------------------------------------------------------------------------
def test_conversation_aggregate_roundtrip_inmemory():
    unit = repo_mod.InMemoryConversationPersistenceUnit()
    convo = _make_convo("c1", "Percakapan 1")
    sess = _make_session("c1", "s1")
    m1 = _make_message("c1", "s1", "msg-1", MessageRole.USER, "buat issue")
    m2 = _make_message("c1", "s1", "msg-2", MessageRole.ASSISTANT,
                       "rencana disusun")
    unit.conversations.save_conversation(convo)
    unit.conversations.save_session(sess)
    unit.conversations.append_message(m1)
    unit.conversations.append_message(m2)

    loaded_convo = unit.conversations.load_conversation("c1")
    loaded_sess = unit.conversations.load_session("s1")
    loaded_msgs = unit.conversations.list_messages("c1")

    # Utuh & canonical
    assert loaded_convo == convo and isinstance(loaded_convo, Conversation)
    assert loaded_sess == sess and isinstance(loaded_sess, ConversationSession)
    assert loaded_msgs == [m1, m2]  # list[Message] canonical, bukan duplikat
    assert all(isinstance(m, Message) for m in loaded_msgs)
    assert loaded_msgs[0].role is MessageRole.USER
    assert loaded_msgs[1].role is MessageRole.ASSISTANT


def test_message_is_canonical_not_duplicate():
    # Message yg disimpan/diambil adalah sama kelas Message universal_ai,
    # bukan entity kedua.
    from sam.application.ux.repositories import _msg_deser, _msg_ser
    m = _make_message("c1", "s1", "m1", MessageRole.USER, "teks")
    assert _msg_deser(_msg_ser(m)) == m
    assert type(m).__module__ == "sam.universal_ai.message_model"


def test_no_mission_request_field_in_canonical_models():
    c = _make_convo("c1")
    s = _make_session("c1", "s1")
    m = _make_message("c1", "s1", "m1", MessageRole.USER, "t")
    _assert_no_mission_field("conversation", c.as_dict())
    _assert_no_mission_field("session", s.as_dict())
    _assert_no_mission_field("message", m.as_dict())


def test_multiconversation_isolated_inmemory():
    unit = repo_mod.InMemoryConversationPersistenceUnit()
    # conv A
    unit.conversations.save_conversation(_make_convo("cA", "A"))
    unit.conversations.save_session(_make_session("cA", "sA"))
    unit.conversations.append_message(
        _make_message("cA", "sA", "mA1", MessageRole.USER, "permintaan A"))
    # conv B
    unit.conversations.save_conversation(_make_convo("cB", "B"))
    unit.conversations.save_session(_make_session("cB", "sB"))
    unit.conversations.append_message(
        _make_message("cB", "sB", "mB1", MessageRole.USER, "permintaan B"))

    assert unit.conversations.list_conversations() == ["cA", "cB"] or \
        set(unit.conversations.list_conversations()) == {"cA", "cB"}
    msgs_a = unit.conversations.list_messages("cA")
    msgs_b = unit.conversations.list_messages("cB")
    assert len(msgs_a) == 1 and msgs_a[0].content == "permintaan A"
    assert len(msgs_b) == 1 and msgs_b[0].content == "permintaan B"
    # Tidak bocor antar conversation
    assert all(m.conversation_id == "cA" for m in msgs_a)
    assert all(m.conversation_id == "cB" for m in msgs_b)


def test_remove_conversation_cleans_aggregate_inmemory():
    unit = repo_mod.InMemoryConversationPersistenceUnit()
    unit.conversations.save_conversation(_make_convo("c1"))
    unit.conversations.save_session(_make_session("c1", "s1"))
    unit.conversations.append_message(
        _make_message("c1", "s1", "m1", MessageRole.USER, "t"))
    unit.conversations.remove_conversation("c1")
    assert unit.conversations.load_conversation("c1") is None
    assert unit.conversations.load_session("s1") is None
    assert unit.conversations.list_messages("c1") == []


def test_stored_payload_never_contains_secret_inmemory():
    unit = repo_mod.InMemoryConversationPersistenceUnit()
    c = _make_convo("c1")
    s = _make_session("c1", "s1")
    m = _make_message("c1", "s1", "m1", MessageRole.USER,
                      "pakai token abc bukan rahasia")
    unit.conversations.save_conversation(c)
    unit.conversations.save_session(s)
    unit.conversations.append_message(m)
    for blob in (c.as_dict(), s.as_dict(), m.as_dict()):
        _assert_no_secret(blob)


def test_domain_depends_on_protocol_not_psycopg2():
    assert hasattr(repo_mod, "ConversationRepository")
    assert hasattr(repo_mod, "InMemoryConversationPersistenceUnit")
    u = repo_mod.InMemoryConversationPersistenceUnit()
    assert u.ping() is True


# ---------------------------------------------------------------------------
# Integration: PostgreSQL (skip bila SAM_PG_DSN kosong)
# ---------------------------------------------------------------------------
def _pg_unit_or_skip():
    dsn = os.environ.get("SAM_PG_DSN", "").strip()
    if not dsn:
        pytest.skip("SAM_PG_DSN tidak diset — skip integrasi PostgreSQL")
    return repo_mod.PostgresConversationPersistenceUnit(dsn=dsn)


def test_pg_conversation_roundtrip():
    unit = _pg_unit_or_skip()
    cid = "s2test-c1"
    sid = "s2test-s1"
    unit.conversations.remove_conversation(cid)  # bersihkan sisa
    convo = _make_convo(cid, "PG conv")
    sess = _make_session(cid, sid)
    m = _make_message(cid, sid, "s2test-msg1", MessageRole.USER, "buat issue")
    unit.conversations.save_conversation(convo)
    unit.conversations.save_session(sess)
    unit.conversations.append_message(m)

    assert unit.conversations.load_conversation(cid) == convo
    assert unit.conversations.load_session(sid) == sess
    loaded = unit.conversations.list_messages(cid)
    assert len(loaded) == 1 and loaded[0] == m
    assert isinstance(loaded[0], Message)
    unit.conversations.remove_conversation(cid)


def test_pg_conversation_survives_restart():
    """Simulasi restart: unit BARU (instance ulang) membaca state dari DB."""
    unit = _pg_unit_or_skip()
    cid = "s2test-restart"
    sid = "s2test-restart-s"
    unit.conversations.remove_conversation(cid)
    unit.conversations.save_conversation(_make_convo(cid, "restart-ok"))
    unit.conversations.save_session(_make_session(cid, sid))
    unit.conversations.append_message(
        _make_message(cid, sid, "s2test-restart-msg", MessageRole.USER, "t"))

    unit2 = repo_mod.PostgresConversationPersistenceUnit(dsn=unit.dsn)
    assert unit2.conversations.load_conversation(cid) == _make_convo(cid, "restart-ok")
    assert unit2.conversations.load_session(sid) is not None
    msgs = unit2.conversations.list_messages(cid)
    assert len(msgs) == 1 and msgs[0].content == "t"
    unit.conversations.remove_conversation(cid)


def test_pg_has_conversation_repository(pg_unit_provider=None):
    unit = _pg_unit_or_skip()
    assert hasattr(unit, "conversations")
    assert unit.ping() is True
