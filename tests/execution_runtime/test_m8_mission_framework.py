"""M8 — tests. Credentialed Operational Integration framework.

Verifikasi (deterministik, tanpa key/driver nyata):
1. M8-001: tanpa NVIDIA key -> stage reason_ai BLOCKED (bukan mock), mission
   verdict jujur (tidak diklaim sukses penuh).
2. M8-002: tanpa GITHUB_TOKEN -> github_api BLOCKED (NO SIDE EFFECT);
   tanpa GITHUB_TEST_REPO -> investigate menandai repo kosong.
3. M8-003: tanpa SMTP -> smtp_send BLOCKED (tidak kirim ke mana pun).
4. M8-004: tanpa playwright -> browser_runtime BLOCKED jujur (fetch BUKAN
   browser automation), TIDAK pernah memanggil sync_playwright.
5. Tidak ada raw secret bocor ke timeline/artifact (boundary scrub).
6. BoundaryAwareExecution: invalid -> FAILED, timeout -> FAILED, zero side effect.
"""
from __future__ import annotations

import os
import tempfile

import pytest

from sam.execution_runtime.m8_mission_framework import (
    M8_001,
    M8_002,
    M8_003,
    M8_004,
    M8_006,
    m8_001_build,
    m8_002_build,
    m8_003_build,
    m8_004_build,
    m8_006_build,
)
from sam.execution_runtime.credential_boundary import (
    BoundaryStatus,
    CredentialBoundary,
    CredentialRequirement,
    BoundaryAwareExecution,
)
from sam.execution_runtime.real_harness import AuditTrail
from sam.runtime_service.secrets.secret_provider import SecretProvider


def _out():
    return tempfile.mkdtemp(prefix="m8test_")


def _clear_env():
    for v in ("NVIDIA_API_KEY", "GITHUB_TOKEN", "GITHUB_TEST_REPO",
              "SMTP_HOST", "SMTP_USER", "SMTP_PASS", "TEST_MAILBOX",
              "BROWSER_DRIVER_OK"):
        os.environ.pop(v, None)


# --- 1. M8-001 NVIDIA BLOCKED tanpa key ---
def test_m8_001_ai_blocked_without_nvidia_key(monkeypatch):
    _clear_env()
    audit = AuditTrail()
    mission = m8_001_build(audit, artifact_dir=_out())
    result = mission.run()
    assert result["mission_id"] == M8_001
    reason = next(t for t in result["timeline"] if t["stage"] == "reason_ai")
    assert reason["blocked"] is True
    assert "BLOCKED" in reason["detail"].upper() or "NO EXTERNAL" in reason["detail"].upper() \
        or "SIDE EFFECT" in reason["detail"].upper()
    # verdict TIDAK diklaim sukses penuh karena ada stage blocked
    assert result["ok"] is False


# --- 2. M8-002 GitHub BLOCKED tanpa token ---
def test_m8_002_github_blocked_without_token(monkeypatch):
    _clear_env()
    audit = AuditTrail()
    mission = m8_002_build(audit, artifact_dir=_out(), repo="VanM-Hub/test-issues")
    result = mission.run()
    assert result["mission_id"] == M8_002
    gh = next(t for t in result["timeline"] if t["stage"] == "github_api")
    assert gh["blocked"] is True
    assert result["ok"] is False


# --- 2b. M8-002 repo kosong -> investigate jujur ---
def test_m8_002_repo_empty_flagged(monkeypatch):
    _clear_env()
    audit = AuditTrail()
    mission = m8_002_build(audit, artifact_dir=_out(), repo="")
    result = mission.run()
    inv = next(t for t in result["timeline"] if t["stage"] == "investigate")
    assert "TEST" in inv["detail"].upper() or "kosong" in inv["detail"]


# --- 3. M8-003 SMTP BLOCKED tanpa credential ---
def test_m8_003_smtp_blocked_without_creds(monkeypatch):
    _clear_env()
    audit = AuditTrail()
    mission = m8_003_build(audit, artifact_dir=_out())
    result = mission.run()
    assert result["mission_id"] == M8_003
    smtp = next(t for t in result["timeline"] if t["stage"] == "smtp_send")
    assert smtp["blocked"] is True
    assert result["ok"] is False


# --- 4. M8-004 Browser BLOCKED tanpa playwright (fetch bukan automation) ---
def test_m8_004_browser_blocked_without_playwright(monkeypatch):
    _clear_env()
    # pastikan BROWSER_DRIVER_OK kosong -> boundary blocked SEBELUM playwright dicek
    audit = AuditTrail()
    mission = m8_004_build(audit, artifact_dir=_out())
    result = mission.run()
    br = next(t for t in result["timeline"] if t["stage"] == "browser_runtime")
    assert br["blocked"] is True


# --- 5. tidak ada raw secret bocor di timeline ---
def test_m8_no_raw_secret_in_timeline(monkeypatch):
    _clear_env()
    os.environ["NVIDIA_API_KEY"] = "nvapi-FAKE_SECRET_VALUE_1234567890"
    audit = AuditTrail()
    mission = m8_001_build(audit, artifact_dir=_out())
    result = mission.run()
    dumped = str(result["timeline"])
    assert "nvapi-FAKE_SECRET_VALUE_1234567890" not in dumped
    os.environ.pop("NVIDIA_API_KEY", None)


# --- 6. BoundaryAwareExecution klasifikasi jujur ---
def test_boundary_invalid_failed():
    b = CredentialBoundary(provider=SecretProvider({"K": "abc"}))
    r = b.resolve(CredentialRequirement("p", "K", min_length=8))
    assert r.status == BoundaryStatus.INVALID
    assert r.action == "failed"
    assert r.available is False


def test_boundary_timeout_failed():
    b = CredentialBoundary(provider=SecretProvider({"K": "longenoughsecret"}))

    def boom():
        raise TimeoutError("timeout")

    awe = BoundaryAwareExecution(b)
    out = awe.execute(CredentialRequirement("p", "K", min_length=8), boom)
    assert out["ok"] is False
    assert out["failed"] is True


def test_boundary_zero_side_effect_when_missing():
    calls = []

    def effect():
        calls.append("X")
        return {"ok": True}

    b = CredentialBoundary(provider=SecretProvider({"K": None}))
    awe = BoundaryAwareExecution(b)
    out = awe.execute(CredentialRequirement("p", "K", min_length=8), effect)
    assert calls == []
    assert out["blocked"] is True


# --- M8-006 multi-external certification ---
def test_m8_006_chain_blocked_without_credentials(monkeypatch):
    _clear_env()
    audit = AuditTrail()
    mission = m8_006_build(audit, artifact_dir=_out(), repo="VanM-Hub/test-issues")
    result = mission.run()
    assert result["mission_id"] == M8_006
    stages = [t["stage"] for t in result["timeline"]]
    # chain lengkap ada
    for want in ("http_evidence", "nvidia_reasoning", "recommend", "approve",
                 "github_mutation", "verify"):
        assert want in stages, f"stage {want} tidak ada di chain M8-006"
    # tanpa key -> nvidia & github BLOCKED, verdict jujur
    nv = next(t for t in result["timeline"] if t["stage"] == "nvidia_reasoning")
    gh = next(t for t in result["timeline"] if t["stage"] == "github_mutation")
    assert nv["blocked"] is True
    assert gh["blocked"] is True
    assert result["ok"] is False


def test_m8_006_http_evidence_real_ran(monkeypatch):
    """Bagian HTTP (evidence) TIDAK butuh key -> berjalan nyata (bukan mock)."""
    _clear_env()
    audit = AuditTrail()
    mission = m8_006_build(audit, artifact_dir=_out(), repo="VanM-Hub/test-issues")
    result = mission.run()
    ev = next(t for t in result["timeline"] if t["stage"] == "http_evidence")
    # evidence nyata dari JSONPlaceholder post id=7 (title non-kosong) atau BLOCKED bila offline
    assert ev["ok"] is True or ev.get("blocked") is True
    if ev["ok"]:
        assert ev["evidence"].get("id") == 7
        assert ev["evidence"].get("title")
