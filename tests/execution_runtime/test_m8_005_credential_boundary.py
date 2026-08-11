"""M8-005 — tests. Production Credential Boundary.

Verifikasi 8 syarat wajib Van (2026-08-12):
  1. credential tidak masuk log
  2. credential tidak masuk audit payload
  3. credential tidak masuk artifact
  4. credential tidak masuk LLM context/prompt
  5. missing credential  -> BLOCKED
  6. invalid credential  -> FAILED
  7. timeout             -> FAILED
  8. no credential       -> zero side effect

Deterministik, tanpa network, tanpa key nyata (env injection via SecretProvider).
"""
from __future__ import annotations

import pytest

from sam.execution_runtime.credential_boundary import (
    BoundaryStatus,
    CredentialBoundary,
    CredentialRequirement,
    BoundaryAwareExecution,
    BoundaryResult,
    SecretScrubber,
)
from sam.runtime_service.secrets.secret_provider import SecretProvider

FAKE_SECRET = "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"


def _env(**kw) -> SecretProvider:
    return SecretProvider({k: v for k, v in kw.items() if v is not None})


def _req(**kw) -> CredentialRequirement:
    base = dict(provider_id="nvidia", env_var="NVIDIA_API_KEY",
                label="NVIDIA", min_length=8, timeout_seconds=3.0, required=True)
    base.update(kw)
    return CredentialRequirement(**base)


# --- 5. missing credential -> BLOCKED ---
def test_missing_credential_is_blocked():
    b = CredentialBoundary(provider=_env(NVIDIA_API_KEY=None))
    r = b.resolve(_req())
    assert r.status == BoundaryStatus.MISSING
    assert r.available is False
    assert r.action == "blocked"
    assert b.audit_log()[0]["status"] == "missing"


# --- 6. invalid credential -> FAILED (terlalu pendek) ---
def test_short_credential_is_failed():
    b = CredentialBoundary(provider=_env(NVIDIA_API_KEY="abc"))
    r = b.resolve(_req(min_length=8))
    assert r.status == BoundaryStatus.INVALID
    assert r.available is False
    assert r.action == "failed"


# --- invalid placeholder -> FAILED ---
def test_placeholder_credential_is_failed():
    b = CredentialBoundary(provider=_env(NVIDIA_API_KEY="your_token_here"))
    r = b.resolve(_req())
    assert r.status == BoundaryStatus.INVALID
    assert r.action == "failed"


# --- 7. timeout -> FAILED (via executor error propagation) ---
def test_timeout_failure_propagates():
    def executor():
        raise TimeoutError("SMTP connection timed out")

    b = CredentialBoundary(provider=_env(NVIDIA_API_KEY=FAKE_SECRET))
    awe = BoundaryAwareExecution(b)
    out = awe.execute(_req(), executor)
    assert out["ok"] is False
    assert out["failed"] is True
    assert out["reason"] == "executor error: TimeoutError"


# --- 8. no credential -> zero side effect (executor TIDAK pernah dipanggil) ---
def test_no_credential_zero_side_effect():
    called = []

    def executor():
        called.append("SIDE_EFFECT!")
        return {"ok": True}

    b = CredentialBoundary(provider=_env(NVIDIA_API_KEY=None))
    awe = BoundaryAwareExecution(b)
    out = awe.execute(_req(), executor)
    assert called == []                    # side effect TIDAK terjadi
    assert out["blocked"] is True
    assert out["action"] == "blocked"


# --- 1. credential tidak masuk log/audit payload ---
def test_credential_not_in_audit_payload():
    b = CredentialBoundary(provider=_env(NVIDIA_API_KEY=FAKE_SECRET))
    r = b.resolve(_req())
    # audit berisi masked, bukan raw
    dumped = str(b.audit_log())
    assert FAKE_SECRET not in dumped
    assert r.masked != FAKE_SECRET
    assert "REDACTED" not in dumped  # masked via mask_secret (bukan REDACTED literal)


# --- 2. credential tidak masuk artifact (scrub) ---
def test_credential_scrubbed_from_artifact():
    scrub = SecretScrubber([FAKE_SECRET])
    artifact = {"result": "ok", "auth_header": f"Bearer {FAKE_SECRET}"}
    cleaned = scrub.scrub_dict(artifact)
    dumped = str(cleaned)
    assert FAKE_SECRET not in dumped
    assert "[REDACTED]" in str(cleaned.get("auth_header")) or \
           ("***" in str(cleaned.get("auth_header")))


# --- 3. credential tidak masuk LLM context/prompt ---
def test_credential_scrubbed_from_prompt():
    scrub = SecretScrubber([FAKE_SECRET])
    prompt = f"Use api key {FAKE_SECRET} to call model"
    cleaned = scrub.scrub(prompt)
    assert FAKE_SECRET not in cleaned
    assert "REDACTED" in cleaned


# --- 4. BoundaryAwareExecution: hasil di-scrub sebelum keluar ---
def test_boundary_aware_scrubs_output():
    b = CredentialBoundary(provider=_env(NVIDIA_API_KEY=FAKE_SECRET))
    awe = BoundaryAwareExecution(b, SecretScrubber([FAKE_SECRET]))

    def executor():
        return {"response": f"token={FAKE_SECRET}", "ok": True}

    out = awe.execute(_req(), executor)
    assert out["ok"] is True
    assert FAKE_SECRET not in str(out)
    assert out["leak_free"] is True
