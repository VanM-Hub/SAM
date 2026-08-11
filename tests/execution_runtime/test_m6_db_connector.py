# -*- coding: utf-8 -*-
"""Test M6-002 - Canonical Universal DB Connector.

Membuktikan connector database kedua Operational Expansion:
- Satu-satunya jalur eksekusi = RealExecutionHarness (no second executor).
- Tanpa mock default: tabel tak dikenal / target kosong / target file tak ada
  -> BLOCKED / RAISE (NO EXTERNAL SIDE EFFECT).
- PREVIEW tidak menyamar sebagai execution (explicit, simulated, 0 calls).
- E2E nyata: SQL SELECT genuine dieksekusi terhadap SQLite, hasil tiap baris
  diverifikasi sesuai kontrak schema. Backend SQLite = nyata (bukan mock).
- Dialektur postgres: kontrak tersedia tapi tanpa driver -> BLOCKED (tidak
  diklaim sebagai sukses).

Cara jalan:
    python -m pytest tests/execution_runtime/test_m6_db_connector.py -v
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.execution_runtime.canonical_db_connector import (
    DEFAULT_SCHEMAS,
    DbConnectorError,
    RealDbAdapter,
    RealDbConnector,
    ensure_demo_sqlite,
)
from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    RealExecutionHarness,
)


@pytest.fixture()
def db_path():
    tmp = tempfile.mkdtemp(prefix="m6db_")
    path = os.path.join(tmp, "demo.db")
    ensure_demo_sqlite(path)
    return path


@pytest.fixture()
def connector():
    return RealDbConnector(audit=AuditTrail())


# ---- Structural: no mock, gate, no second executor ----

def test_m6db_no_second_executor():
    """Connector BUKAN executor: hanya lewat harness canonical."""
    c = RealDbConnector(audit=AuditTrail())
    assert hasattr(c, "_harness")
    assert isinstance(c._harness, RealExecutionHarness)
    assert not hasattr(c, "execute_without_harness")


def test_m6db_table_unknown_blocked(connector, db_path):
    """Tabel tak dikenal -> boundary gate FAIL -> BLOCKED (no call)."""
    result = connector.execute("tidak_ada_tabel", db_path, mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 unknown")
    assert result.get("ok") is False
    assert result.get("blocked") is True
    assert "boundary" in result.get("blocked_by", [])
    assert result.get("external_calls") == 0


def test_m6db_target_missing_blocked(connector):
    """Target db kosong -> target gate FAIL -> BLOCKED."""
    result = connector.execute("users", "", mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 no target")
    assert result.get("ok") is False
    assert "target_db" in result.get("blocked_by", [])


def test_m6db_target_file_not_exist_blocked(connector):
    """Target path tak ada (file tidak ada) -> BLOCKED (no fake success)."""
    result = connector.execute("users", os.path.join(tempfile.gettempdir(), "m6_none.db"),
                               mode=ExecutionMode.EXECUTE, approval_reason="M6 no file")
    assert result.get("ok") is False
    assert "target_db" in result.get("blocked_by", [])


def test_m6db_preview_is_not_execution(connector, db_path):
    """PREVIEW = explicit simulated, TIDAK menyamar eksekusi."""
    result = connector.execute("users", db_path, mode=ExecutionMode.PREVIEW,
                               approval_reason="M6 preview")
    assert result.get("mode") == "PREVIEW"
    assert result.get("simulated") is True
    assert result.get("external_calls") == 0
    assert "count" not in result  # tidak ada query nyata


def test_m6db_sqlite_genuine_not_mock(connector, db_path):
    """SELECT nyata terhadap SQLite: hasil sesuai data sebenarnya (bukan hardcode)."""
    result = connector.execute("users", db_path, mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 real sqlite")
    assert result.get("ok") is True
    rows = result.get("rows", [])
    assert len(rows) == 3  # data asli dari ensure_demo_sqlite
    names = {r["name"] for r in rows}
    assert names == {"Aster", "Zara", "VanM"}  # data nyata, bukan mock


def test_m6db_posts_table(connector, db_path):
    """Tabel kedua: SELECT posts nyata, verifikasi kontrak kolom."""
    result = connector.execute("posts", db_path, mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 posts")
    assert result.get("ok") is True
    rows = result.get("rows", [])
    assert len(rows) == 2
    assert "title" in rows[0] and "body" in rows[0]


def test_m6db_limit_works(connector, db_path):
    """Limit diterapkan: SELECT LIMIT 1 -> 1 baris."""
    result = connector.execute("users", db_path, mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 limit", limit=1)
    assert result.get("ok") is True
    assert result.get("count") == 1


def test_m6db_postgres_not_claimed(connector):
    """PostgreSQL: kontrak ada tapi tanpa driver/koneksi -> TIDAK diklaim sukses.

    Connector backend-agnostik; dialektur tanpa driver tidak boleh menipu
    menjadi 'berhasil'. KLaim hanya untuk backend yang benar-benar terverifikasi.
    """
    # connector hanya mendaftarkan tabel sqlite (schema); postgres bukan capability
    result = connector.execute("users", "postgres://nouser@nohost/db",
                               mode=ExecutionMode.EXECUTE, approval_reason="M6 pg")
    # must not be a fake success: either blocked (target bukan file) atau error
    assert result.get("ok") is False


def test_m6db_audit_and_verification(connector, db_path):
    """Eksekusi nyata tercatat di audit (call -> sql -> result)."""
    audit = connector._audit  # noqa: SLF001
    connector.execute("users", db_path, mode=ExecutionMode.EXECUTE,
                      approval_reason="M6 audit")
    actions = [e.action for e in audit.entries]
    assert any(a == "db.connector.call" for a in actions)
    assert any(a == "db.connector.sql" for a in actions)
    assert any(a == "db.connector.result" for a in actions)
