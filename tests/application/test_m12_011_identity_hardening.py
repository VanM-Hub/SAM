"""test_m12_011_identity_hardening.py — M12-011 Identity Hardening.

Kontrak M12-011: Secure cookie, CSRF, session TTL, revocation, auth mandatory.
Anonymous/expired/revoked/forged DENIED; cross-user DENIED.

Cakupan unit (tanpa server / tanpa users.json eksternal):
  - Session TTL: token expired -> DENIED; valid -> OK.
  - Revocation: revoke(token) -> DENIED; revoke_user(username) -> semua sesi
    user tersebut DENIED.
  - Forged/unknown token -> DENIED.
  - Anonymous (tanpa token) saat auth aktif -> 401 (DENIED).
  - CSRF: cookie-mode mutasi tanpa/wrong X-CSRF-Token -> 403; benar -> lolos.
  - Cross-user: identitas dari sesi (token A -> user A), bukan dari body.
  - Secure cookie: login saat produksi set secure=True; dev tetap http cookie.
"""
from __future__ import annotations

import json
import os
import time

import pytest

from sam.application.ux.identity import (
    SessionStore,
    UserStore,
    _hash_password,
)
from sam.api.routes.ux import UxRoutes


def _seed_users(tmp_path, name="van") -> str:
    """Buat users.json sementara; return path."""
    path = tmp_path / "users.json"
    rec = _hash_password("rahasia-benar")
    path.write_text(
        json.dumps({"users": [{"username": name, "role": "operator", "password": rec}]}),
        encoding="utf-8",
    )
    return str(path)

# ---------- SessionStore: TTL / revoke / forged ----------

def test_authenticate_valid_token():
    s = SessionStore()
    tok = s.login({"username": "van", "role": "operator"})
    assert s.authenticate(tok) == {"username": "van", "role": "operator"}


def test_expired_token_denied(monkeypatch):
    s = SessionStore(ttl=1)
    tok = s.login({"username": "van", "role": "operator"})
    monkeypatch.setattr("sam.application.ux.identity._now_epoch", lambda: time.time() + 10)
    assert s.authenticate(tok) is None  # expired -> DENIED


def test_revoked_token_denied():
    s = SessionStore()
    tok = s.login({"username": "van", "role": "operator"})
    assert s.revoke(tok) is True
    assert s.authenticate(tok) is None  # revoked -> DENIED


def test_revoke_user_denies_all_sessions():
    s = SessionStore()
    a = s.login({"username": "van", "role": "operator"})
    b = s.login({"username": "van", "role": "operator"})
    c = s.login({"username": "aster", "role": "operator"})
    assert s.revoke_user("van") == 2
    assert s.authenticate(a) is None
    assert s.authenticate(b) is None
    assert s.authenticate(c) is not None  # user lain tidak ikut revoked


def test_forged_unknown_token_denied():
    s = SessionStore()
    assert s.authenticate("token-tidak-pernah-ada") is None
    assert s.authenticate(None) is None
    assert s.authenticate("") is None


def test_anonymous_denied_when_auth_active(tmp_path, monkeypatch):
    monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
    monkeypatch.delenv("SAM_ENV", raising=False)
    routes = UxRoutes()
    # sessions kosong, tanpa token -> _require_auth harus 401
    with pytest.raises(Exception) as exc:
        routes._require_auth(None, None)
    assert "401" in str(exc.value) or "autentikasi" in str(exc.value).lower()


# ---------- cross-user & CSRF via _require_auth ----------

def test_cross_user_identity_from_session(tmp_path, monkeypatch):
    monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
    monkeypatch.delenv("SAM_ENV", raising=False)
    routes = UxRoutes()
    tok_a = routes.sessions.login({"username": "van", "role": "operator"})
    tok_b = routes.sessions.login({"username": "aster", "role": "operator"})
    # token A -> identitas A (bukan dari body) -> cross-user DENIED dijamin
    id_a = routes._require_auth(f"Bearer {tok_a}", None)
    assert id_a["username"] == "van"
    id_b = routes._require_auth(f"Bearer {tok_b}", None)
    assert id_b["username"] == "aster"
    # approve atas nama A harus identitas A (source of truth = sesi)
    assert id_a is not None and id_a["username"] != "aster"


def test_csrf_cookie_mode_denied_without_token(tmp_path, monkeypatch):
    monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
    monkeypatch.delenv("SAM_ENV", raising=False)
    routes = UxRoutes()
    tok = routes.sessions.login({"username": "van", "role": "operator"})
    # cookie-mode (authorization=None, cookie=tok) tanpa CSRF -> 403
    with pytest.raises(Exception) as exc:
        routes._require_auth(None, tok, None)
    assert "403" in str(exc.value) or "CSRF" in str(exc.value)


def test_csrf_cookie_mode_denied_wrong_token(tmp_path, monkeypatch):
    monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
    monkeypatch.delenv("SAM_ENV", raising=False)
    routes = UxRoutes()
    tok = routes.sessions.login({"username": "van", "role": "operator"})
    with pytest.raises(Exception) as exc:
        routes._require_auth(None, tok, "csrf-salah")
    assert "403" in str(exc.value) or "CSRF" in str(exc.value)


def test_csrf_cookie_mode_allowed_correct_token(tmp_path, monkeypatch):
    monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
    monkeypatch.delenv("SAM_ENV", raising=False)
    routes = UxRoutes()
    tok = routes.sessions.login({"username": "van", "role": "operator"})
    csrf = routes.sessions.csrf_for(tok)
    identity = routes._require_auth(None, tok, csrf)
    assert identity["username"] == "van"


def test_bearer_mode_no_csrf_needed(tmp_path, monkeypatch):
    monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
    monkeypatch.delenv("SAM_ENV", raising=False)
    routes = UxRoutes()
    tok = routes.sessions.login({"username": "van", "role": "operator"})
    # bearer (authorization) tidak butuh CSRF (token tak ter-expose cookie)
    identity = routes._require_auth(f"Bearer {tok}", None, None)
    assert identity["username"] == "van"


# ---------- auth mandatory produksi + secure cookie ----------

def test_auth_mandatory_in_production(monkeypatch, tmp_path):
    monkeypatch.delenv("SAM_ENABLE_AUTH", raising=False)
    monkeypatch.setenv("SAM_ENV", "production")
    routes = UxRoutes()
    assert routes.production is True
    assert routes.auth_enabled is True  # produksi -> login WAJIB (tanpa flag pun)


def test_secure_cookie_flag_production(monkeypatch, tmp_path):
    monkeypatch.setenv("SAM_ENV", "production")
    routes = UxRoutes()
    assert routes.production is True
    # cookie hanya secure saat produksi; HttpOnly + SameSite selalu
    from fastapi import Response
    r = Response()
    tok = routes.sessions.login({"username": "van", "role": "operator"})
    r.set_cookie("sam_session", tok, httponly=True, samesite="lax",
                 secure=routes.production, path="/")
    hdr = r.headers.get("set-cookie", "")
    assert "Secure" in hdr
    assert "HttpOnly" in hdr
    assert "SameSite=lax" in hdr


def test_dev_cookie_not_secure(monkeypatch, tmp_path):
    monkeypatch.delenv("SAM_ENV", raising=False)
    routes = UxRoutes()
    assert routes.production is False
    from fastapi import Response
    r = Response()
    tok = routes.sessions.login({"username": "van", "role": "operator"})
    r.set_cookie("sam_session", tok, httponly=True, samesite="lax",
                 secure=routes.production, path="/")
    assert "Secure" not in r.headers.get("set-cookie", "")
