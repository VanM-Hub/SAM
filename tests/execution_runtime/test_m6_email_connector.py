# -*- coding: utf-8 -*-
"""Test M6-004 - Canonical Universal Email Connector.

Membuktikan connector email keempat Operational Expansion:
- Satu-satunya jalur eksekusi = RealExecutionHarness (no second executor).
- Tanpa mock: kirim nyata tanpa SMTP terkonfigurasi -> BLOCKED (NO SIDE EFFECT).
- dry_run = VALIDASI eksplisit (sent:false), bukan mock sukses / tidak menyamar
  sebagai kirim nyata.
- Validas format email nyata (regex), tanp apalagi kontrak kosong -> GAGAL.
- PREVIEW != execution.

Jalankan:
    python -m pytest tests/execution_runtime/test_m6_email_connector.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.execution_runtime.canonical_email_connector import (
    EmailConnectorError,
    RealEmailAdapter,
    RealEmailConnector,
    is_valid_email,
)
from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    RealExecutionHarness,
)


@pytest.fixture()
def connector():
    return RealEmailConnector(audit=AuditTrail())


def _params():
    return {"sender": "zara@sam.local", "recipient": "van@sam.local",
            "subject": "M6 test", "body": "hello canonical"}


# ---- Structural ----

def test_m6email_no_second_executor():
    """Connector BUKAN executor: hanya lewat harness canonical."""
    c = RealEmailConnector(audit=AuditTrail())
    assert hasattr(c, "_harness")
    assert isinstance(c._harness, RealExecutionHarness)
    assert not hasattr(c, "execute_without_harness")


def test_m6email_op_unknown_blocked(connector):
    """Operasi tak dikenal -> boundary FAIL -> BLOCKED."""
    result = connector.execute("spam_everyone", {}, mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 bad op")
    assert result.get("ok") is False
    assert result.get("blocked") is True
    assert "boundary" in result.get("blocked_by", [])


def test_m6email_preview_is_not_execution(connector):
    """PREVIEW explicit simulated, 0 external calls."""
    result = connector.execute("send", _params(), mode=ExecutionMode.PREVIEW,
                               approval_reason="M6 preview")
    assert result.get("mode") == "PREVIEW"
    assert result.get("simulated") is True
    assert result.get("external_calls") == 0


# ---- Validasi email ----

def test_email_regex_valid():
    assert is_valid_email("user@example.com")
    assert is_valid_email("a.b+c@sub.domain.co.id")


def test_email_regex_invalid():
    assert not is_valid_email("")
    assert not is_valid_email("not-an-email")
    assert not is_valid_email("user@nodot")


# ---- dry_run = validasi eksplisit, bukan kirim, bukan mock sukses ----

def test_m6email_dry_run_no_smtp_ok(connector, monkeypatch):
    """dry_run valid meski tanpa SMTP: hasil validasi, sent:false, jelas."""
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"):
        monkeypatch.delenv(k, raising=False)
    result = connector.execute("send", _params(), mode=ExecutionMode.EXECUTE,
                               dry_run=True, approval_reason="M6 dry run")
    assert result.get("ok") is True
    assert result.get("dry_run") is True
    assert result.get("sent") is False  # jujur: tidak ada email terkirim
    assert result.get("mode") == "DRY_RUN"  # tanda eksplisit validasi


def test_m6email_send_no_smtp_blocked(connector, monkeypatch):
    """Kirim NYATA tanpa SMTP terkonfigurasi -> BLOCKED (NO SIDE EFFECT)."""
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"):
        monkeypatch.delenv(k, raising=False)
    result = connector.execute("send", _params(), mode=ExecutionMode.EXECUTE,
                               dry_run=False, approval_reason="M6 real send no smtp")
    assert result.get("ok") is False
    assert "credential_email" in result.get("blocked_by", [])


def test_m6email_invalid_sender_raises():
    """sender tidak valid -> adapter RAISE (no fake success)."""
    adapter = RealEmailAdapter(AuditTrail())
    with pytest.raises(EmailConnectorError):
        adapter.execute("not-email", "van@sam.local", "s", "b", dry_run=True)


def test_m6email_validate_op(connector):
    """Operasi validate: valid/tidak tanpa kirim, tanpa SMTP."""
    ok = connector.execute("validate", {"email": "a@b.com"}, mode=ExecutionMode.EXECUTE,
                           approval_reason="M6 validate")
    assert ok.get("ok") is True and ok.get("valid") is True
    bad = connector.execute("validate", {"email": "nope"}, mode=ExecutionMode.EXECUTE,
                            approval_reason="M6 validate bad")
    assert bad.get("ok") is False and bad.get("valid") is False


def test_m6email_audit_dry_run(connector, monkeypatch):
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"):
        monkeypatch.delenv(k, raising=False)
    audit = connector._audit  # noqa: SLF001
    connector.execute("send", _params(), mode=ExecutionMode.EXECUTE, dry_run=True,
                      approval_reason="M6 audit")
    actions = [e.action for e in audit.entries]
    assert any(a == "email.connector.dry_run" for a in actions)
