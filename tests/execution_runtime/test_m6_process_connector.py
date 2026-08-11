# -*- coding: utf-8 -*-
"""Test M6-003 - Canonical Universal Process Connector.

Membuktikan connector proses ketiga Operational Expansion:
- Satu-satunya jalur eksekusi = RealExecutionHarness (no second executor).
- Tanpa mock default / bukan free-run: command tak dikenal -> BLOCKED (allowlist).
- READ-ONLY: hanya command observasi; PREVIEW != execution.
- E2E nyata: subprocess dieksekusi (hostname/python_version), exit code 0 +
  stdout diverifikasi.

Jalankan:
    python -m pytest tests/execution_runtime/test_m6_process_connector.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.execution_runtime.canonical_process_connector import (
    READONLY_COMMANDS,
    ProcessConnectorError,
    RealProcessAdapter,
    RealProcessConnector,
)
from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    RealExecutionHarness,
)


@pytest.fixture()
def connector():
    return RealProcessConnector(audit=AuditTrail())


# ---- Structural ----

def test_m6proc_no_second_executor():
    """Connector BUKAN executor: hanya lewat harness canonical."""
    c = RealProcessConnector(audit=AuditTrail())
    assert hasattr(c, "_harness")
    assert isinstance(c._harness, RealExecutionHarness)
    assert not hasattr(c, "execute_without_harness")


def test_m6proc_command_unknown_blocked(connector):
    """Command tak dikenal -> boundary FAIL -> BLOCKED (no call)."""
    result = connector.execute("rm_rf_root", mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 bad cmd")
    assert result.get("ok") is False
    assert result.get("blocked") is True
    assert "boundary" in result.get("blocked_by", [])


def test_m6proc_allowlist_only():
    """Connector HANYA menjalankan command dalam allowlist read-only."""
    for name in READONLY_COMMANDS:
        # semua yang didaftarkan wajib read-only (tidak ada rm/del/write/format)
        assert not any(bad in name for bad in ("rm", "del", "format", "write", ">", "|"))


def test_m6proc_preview_is_not_execution(connector):
    """PREVIEW explicit simulated, 0 external calls, tidak ada stdout nyata."""
    result = connector.execute("hostname", mode=ExecutionMode.PREVIEW,
                               approval_reason="M6 preview")
    assert result.get("mode") == "PREVIEW"
    assert result.get("simulated") is True
    assert result.get("external_calls") == 0
    assert "stdout" not in result


# ---- E2E real ----

def test_m6proc_hostname(connector):
    """hostname dieksekusi nyata -> exit 0 + stdout non-kosong."""
    result = connector.execute("hostname", mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 hostname")
    assert result.get("ok") is True
    assert result.get("exit_code") == 0
    assert result.get("stdout", "").strip()  # nama host asli


def test_m6proc_python_version(connector):
    """python --version dieksekusi nyata -> exit 0 + versi."""
    result = connector.execute("python_version", mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 python version")
    assert result.get("ok") is True
    assert result.get("exit_code") == 0
    assert "Python" in result.get("stdout", "") or "python" in result.get("stdout", "").lower()


def test_m6proc_audit_and_verification(connector):
    """Eksekusi nyata tercatat di audit (call -> result)."""
    audit = connector._audit  # noqa: SLF001
    connector.execute("hostname", mode=ExecutionMode.EXECUTE,
                      approval_reason="M6 audit")
    actions = [e.action for e in audit.entries]
    assert any(a == "proc.connector.call" for a in actions)
    assert any(a == "proc.connector.result" for a in actions)
