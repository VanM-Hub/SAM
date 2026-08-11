# -*- coding: utf-8 -*-
"""Test M6-001 - Canonical HTTP Universal Connector.

Membuktikan connector pertama Operational Expansion:
- Satu-satunya jalur eksekusi = RealExecutionHarness (no second executor).
- Tanpa mock default: endpoint tak dikenal / param wajib kosong / kredensial
  kosong -> RAISE / BLOCKED (NO EXTERNAL SIDE EFFECT).
- PREVIEW tidak menyamar sebagai execution (explicit, simulated, 0 calls).
- E2E nyata: minimal 2 external API BERBEDA (JSONPlaceholder + httpbin)
  -> HTTP 200, JSON valid, terverifikasi, teraudit.

Cara jalan:
    python -m pytest tests/execution_runtime/test_m6_http_connector.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

import httpx

from sam.execution_runtime.canonical_http_connector import (
    DEFAULT_HTTP_ENDPOINTS,
    HttpConnectorError,
    RealHttpConnector,
    RealHttpAdapter,
)
from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    RealExecutionHarness,
)


def _online() -> bool:
    try:
        r = httpx.get("https://httpbin.org/get", timeout=8)
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


ONLINE = _online()


@pytest.fixture()
def connector():
    return RealHttpConnector(audit=AuditTrail())


@pytest.fixture()
def target_id():
    return "1"


# ---- Structural: no mock default, gate, no second executor ----

def test_m6_no_second_executor():
    """Connector BUKAN executor: eksekusi hanya lewat harness canonical."""
    c = RealHttpConnector(audit=AuditTrail())
    # connector tidak mengekspos adapter eksekusi langsung selain lewat harness
    assert hasattr(c, "_harness")
    assert isinstance(c._harness, RealExecutionHarness)
    assert not hasattr(c, "execute_without_harness")


def test_m6_endpoint_unknown_blocked(connector):
    """Endpoint tak dikenal -> boundary gate FAIL -> BLOCKED (no call)."""
    result = connector.execute("tidak_ada", {}, mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 unknown")
    assert result.get("ok") is False
    assert result.get("blocked") is True
    assert "boundary" in result.get("blocked_by", [])
    assert result.get("external_calls") == 0


def test_m6_param_required_missing_raises(connector):
    """Endpoint butuh id tapi id kosong -> adapter RAISE (no fake success)."""
    adapter = RealHttpAdapter(AuditTrail(), DEFAULT_HTTP_ENDPOINTS)
    with pytest.raises(HttpConnectorError):
        adapter.execute("jsonplaceholder_post", {})  # id wajib, tidak ada


def test_m6_preview_is_not_execution(connector, target_id):
    """PREVIEW = explicit simulated, TIDAK menyamar sebagai execution."""
    result = connector.execute("jsonplaceholder_post", {"id": target_id},
                               mode=ExecutionMode.PREVIEW, approval_reason="M6 preview")
    assert result.get("mode") == "PREVIEW"
    assert result.get("simulated") is True
    assert result.get("external_calls") == 0
    assert "http_status" not in result  # tidak ada HTTP nyata


def test_m6_auth_endpoint_without_key_blocked(connector, monkeypatch):
    """Endpoint ber-auth tanpa key di env -> credential gate FAIL -> BLOCKED."""
    monkeypatch.delenv("M6_TEST_KEY", raising=False)
    # endpoint ber-auth sintetis
    c = RealHttpConnector(
        audit=AuditTrail(),
        endpoints=tuple(DEFAULT_HTTP_ENDPOINTS) + (
            type("E", (), {"name": "needskey", "method": "GET",
                            "url_template": "https://example.test/x", "auth_env": "M6_TEST_KEY",
                            "required_params": (), "description": "", "timeout_seconds": 10.0})(),
        ),
    )
    result = c.execute("needskey", {}, mode=ExecutionMode.EXECUTE,
                       approval_reason="M6 auth missing")
    assert result.get("ok") is False
    assert "credential_http" in result.get("blocked_by", [])


# ---- E2E real (2+ external API berbeda) ----

@pytest.mark.skipif(not ONLINE, reason="offline: skip E2E HTTP nyata")
def test_m6_e2e_jsonplaceholder_post(connector, target_id):
    """API #1: JSONPlaceholder GET /posts/1 -> HTTP 200, JSON valid, terverifikasi."""
    result = connector.execute("jsonplaceholder_post", {"id": target_id},
                               mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 E2E jsonplaceholder post")
    assert result.get("ok") is True
    assert result.get("http_status") == 200
    data = result.get("data", {})
    assert isinstance(data, dict) and data.get("id") == int(target_id)
    assert "title" in data  # kontrak real JSONPlaceholder


@pytest.mark.skipif(not ONLINE, reason="offline: skip E2E HTTP nyata")
def test_m6_e2e_httpbin(connector):
    """API #2: httpbin GET -> HTTP 200, respons echo nyata, terverifikasi."""
    result = connector.execute("httpbin_get", {}, mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 E2E httpbin")
    assert result.get("ok") is True
    assert result.get("http_status") == 200
    data = result.get("data", {})
    assert isinstance(data, dict)
    assert "url" in data  # httpbin echo selalu punya 'url'
    assert data["url"] == "https://httpbin.org/get"


@pytest.mark.skipif(not ONLINE, reason="offline: skip E2E HTTP nyata")
def test_m6_e2e_jsonplaceholder_user(connector):
    """API #1 host lain: JSONPlaceholder GET /users/1 -> HTTP 200, terverifikasi."""
    result = connector.execute("jsonplaceholder_user", {"id": "1"},
                               mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 E2E jsonplaceholder user")
    assert result.get("ok") is True
    assert result.get("http_status") == 200
    data = result.get("data", {})
    assert isinstance(data, dict) and data.get("id") == 1
    assert "email" in data  # kontrak real JSONPlaceholder /users


@pytest.mark.skipif(not ONLINE, reason="offline: skip E2E HTTP nyata")
def test_m6_e2e_audit_and_verification(connector, target_id):
    """Eksekusi nyata tercatat di audit (call -> response -> result)."""
    audit = connector._audit  # noqa: SLF001
    connector.execute("jsonplaceholder_post", {"id": target_id},
                      mode=ExecutionMode.EXECUTE,
                      approval_reason="M6 audit check")
    actions = [e.action for e in audit.entries]
    assert any(a == "http.connector.call" for a in actions)
    assert any(a == "http.connector.response" for a in actions)
    assert any(a == "http.connector.result" for a in actions)
