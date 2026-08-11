# -*- coding: utf-8 -*-
"""Test M6-005 - Canonical Universal Browser Connector.

Membuktikan connector browser kelima Operational Expansion:
- Satu-satunya jalur eksekusi = RealExecutionHarness (no second executor).
- Tanpa mock: URL invalid / operasi tak dikenal -> BLOCKED (NO SIDE EFFECT).
- fetch_url = HTTP nyata read-only; PREVIEW != execution.
- render tanpa driver (playwright/selenium) -> BLOCKED, TIDAK diklaim sukses.

Jalankan:
    python -m pytest tests/execution_runtime/test_m6_browser_connector.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

import httpx

from sam.execution_runtime.canonical_browser_connector import (
    BrowserConnectorError,
    RealBrowserAdapter,
    RealBrowserConnector,
    is_valid_https_url,
    _browser_driver_available,
)
from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    RealExecutionHarness,
)


def _online() -> bool:
    try:
        return httpx.get("https://httpbin.org/html", timeout=8).status_code == 200
    except Exception:  # noqa: BLE001
        return False


ONLINE = _online()


@pytest.fixture()
def connector():
    return RealBrowserConnector(audit=AuditTrail())


# ---- Structural ----

def test_m6browser_no_second_executor():
    """Connector BUKAN executor: hanya lewat harness canonical."""
    c = RealBrowserConnector(audit=AuditTrail())
    assert hasattr(c, "_harness")
    assert isinstance(c._harness, RealExecutionHarness)
    assert not hasattr(c, "execute_without_harness")


def test_m6browser_op_unknown_blocked(connector):
    """Operasi tak dikenal -> boundary FAIL -> BLOCKED."""
    result = connector.execute("exploit", "https://example.com", mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 bad op")
    assert result.get("ok") is False
    assert result.get("blocked") is True
    assert "boundary" in result.get("blocked_by", [])


def test_m6browser_preview_is_not_execution(connector):
    """PREVIEW explicit simulated, 0 external calls."""
    result = connector.execute("fetch_url", "https://httpbin.org/html",
                               mode=ExecutionMode.PREVIEW, approval_reason="M6 preview")
    assert result.get("mode") == "PREVIEW"
    assert result.get("simulated") is True
    assert result.get("external_calls") == 0
    assert "fetch_real" not in result


# ---- URL validation ----

def test_m6browser_url_valid():
    assert is_valid_https_url("https://example.com")
    assert is_valid_https_url("https://sub.example.org/path?q=1")


def test_m6browser_url_invalid():
    assert not is_valid_https_url("")
    assert not is_valid_https_url("http://example.com")  # wajib https
    assert not is_valid_https_url("https://")            # tanpa host
    assert not is_valid_https_url("not a url")


def test_m6browser_invalid_url_fetch_fails(connector):
    """fetch URL invalid -> GAGAL (bukan sukses palsu)."""
    result = connector.execute("fetch_url", "http://insecure", mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 bad url")
    assert result.get("ok") is False
    assert result.get("verification_failed") is True


# ---- render zonder driver -> BLOCKED (jujur) ----

def test_m6browser_render_without_driver_blocked(connector, monkeypatch):
    """render tanpa playwright/selenium -> BLOCKED (TIDAK diklaim sukses)."""
    monkeypatch.setattr("sam.execution_runtime.canonical_browser_connector._browser_driver_available",
                        lambda: False)
    result = connector.execute("render", "https://example.com", mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 render no driver")
    # boleh BLOCKED (gate driver) ATAU verification_failed (adapter raise)
    assert result.get("ok") is False


# ---- E2E real fetch (skip offline) ----

@pytest.mark.skipif(not ONLINE, reason="offline: skip fetch real")
def test_m6browser_fetch_real(connector):
    """fetch_url NYCATA ke httpbin -> 200, HTML non-kosong, terverifikasi."""
    result = connector.execute("fetch_url", "https://httpbin.org/html",
                               mode=ExecutionMode.EXECUTE,
                               approval_reason="M6 fetch real")
    assert result.get("ok") is True
    assert result.get("http_status") == 200
    assert result.get("fetch_real") is True
    assert result.get("html_len", 0) > 0
    assert result.get("content_type", "")


@pytest.mark.skipif(not ONLINE, reason="offline: skip fetch real")
def test_m6browser_fetch_audit(connector):
    """fetch nyata tercatat di audit (fetch -> result)."""
    audit = connector._audit  # noqa: SLF001
    connector.execute("fetch_url", "https://httpbin.org/html", mode=ExecutionMode.EXECUTE,
                      approval_reason="M6 audit")
    actions = [e.action for e in audit.entries]
    assert any(a == "browser.connector.fetch" for a in actions)
    assert any(a == "browser.connector.result" for a in actions)
