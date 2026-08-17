"""test_identity.py — SAM Production Identity (M11-004).

Unit + integrasi:
  - UserStore: verifikasi password (hash), file di luar project (tmp), role.
  - SessionStore: login -> token; authenticate; logout; token invalid.
  - Authorization: can_operate operator/admin True, viewer/unknown False.
  - Route (AUTH aktif): /ux/decide tanpa token -> 401; login+token -> approve
    memakai IDENTITAS SESI (bukan `approver` body); /ux/me; logout invalidates.
  - Regresi: mode AUTH nonaktif -> /ux/decide tetap terima approver body (lama).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sam.application.ux.identity import SessionStore, UserStore, _hash_password


@pytest.fixture
def users_file(tmp_path):
    """Buat users.json sementara (di luar project) dengan 2 user: operator + viewer."""
    hashed = _hash_password("s3cr3t-pass")
    path = tmp_path / "users.json"
    path.write_text(json.dumps({
        "users": [
            {"username": "van", "role": "operator",
             "password": _hash_password("pass-van")},
            {"username": "penonton", "role": "viewer",
             "password": _hash_password("pass-view")},
        ]
    }), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Unit: UserStore
# ---------------------------------------------------------------------------
class TestUserStore:
    def test_verify_ok(self, users_file):
        u = UserStore(path=str(users_file))
        ident = u.verify("van", "pass-van")
        assert ident == {"username": "van", "role": "operator"}

    def test_verify_wrong_password(self, users_file):
        u = UserStore(path=str(users_file))
        assert u.verify("van", "salah") is None

    def test_verify_unknown_user(self, users_file):
        u = UserStore(path=str(users_file))
        assert u.verify("tidak-ada", "pass-van") is None

    def test_hash_not_plaintext(self, users_file):
        raw = users_file.read_text(encoding="utf-8")
        # password asli tidak boleh muncul (hash pbkdf2), tidak ada "no_plain"
        assert "pass-van" not in raw
        assert json.loads(raw)["users"][0]["password"]["hash"]

    def test_file_missing_returns_none(self, tmp_path):
        u = UserStore(path=str(tmp_path / "none.json"))
        assert u.verify("x", "y") is None

    def test_create_user_adds_and_verifies(self, tmp_path):
        path = tmp_path / "users.json"
        u = UserStore(path=str(path))
        ident = u.create_user("ali", "rahasia-1")
        assert ident == {"username": "ali", "role": "operator"}
        # file dibuat + user bisa login
        assert path.exists()
        assert u.verify("ali", "rahasia-1") == {"username": "ali", "role": "operator"}
        # password tidak plaintext di file
        raw = path.read_text(encoding="utf-8")
        assert "rahasia-1" not in raw

    def test_create_user_does_not_overwrite_existing(self, users_file):
        path = Path(users_file)
        u = UserStore(path=str(path))
        id2 = u.create_user("baru", "pass-baru12")
        assert id2["username"] == "baru"
        # user lama tetap valid
        assert u.verify("van", "pass-van") == {"username": "van", "role": "operator"}
        assert u.verify("baru", "pass-baru12")

    def test_create_user_duplicate_raises(self, users_file):
        u = UserStore(path=str(users_file))
        with pytest.raises(ValueError):
            u.create_user("van", "pass-abcdef")

    def test_create_user_short_password_raises(self, tmp_path):
        u = UserStore(path=str(tmp_path / "users.json"))
        with pytest.raises(ValueError):
            u.create_user("x", "123")


# ---------------------------------------------------------------------------
# Unit: SessionStore + Authorization
# ---------------------------------------------------------------------------
class TestSessionStore:
    def test_login_authenticate_roundtrip(self, users_file):
        u = UserStore(path=str(users_file))
        s = SessionStore()
        ident = u.verify("van", "pass-van")
        token = s.login(ident)
        assert token
        got = s.authenticate(token)
        assert got == {"username": "van", "role": "operator"}

    def test_authenticate_invalid(self):
        s = SessionStore()
        assert s.authenticate("bogus-token") is None
        assert s.authenticate(None) is None

    def test_logout_invalidates(self, users_file):
        u = UserStore(path=str(users_file))
        s = SessionStore()
        token = s.login(u.verify("van", "pass-van"))
        assert s.logout(token) is True
        assert s.authenticate(token) is None
        assert s.logout(token) is False

    def test_unique_tokens(self, users_file):
        u = UserStore(path=str(users_file))
        s = SessionStore()
        ident = u.verify("van", "pass-van")
        t1 = s.login(ident)
        t2 = s.login(ident)
        assert t1 != t2


class TestAuthorization:
    def test_can_operate(self):
        u = UserStore(path="::gak-ada::")
        assert u.can_operate("operator") is True
        assert u.can_operate("admin") is True   # siap diperluas
        assert u.can_operate("viewer") is False
        assert u.can_operate("") is False


# ---------------------------------------------------------------------------
# Integrasi route (AUTH aktif / nonaktif)
# ---------------------------------------------------------------------------
@pytest.fixture
def ux_router(users_file, monkeypatch):
    """UxRoutes dengan users file tmp; kembalikan objek route + client test."""
    from fastapi.testclient import TestClient
    from sam.api.routes import ux as ux_mod
    from sam.api.server import app

    # alihkan UserStore instance global ke file tmp
    ux_mod._routes.users._path = users_file
    ux_mod._routes.sessions = SessionStore()
    return ux_mod, TestClient(app), users_file


class TestAuthRoute:
    def test_decide_requires_auth_when_enabled(self, ux_router, monkeypatch):
        ux_mod, client, _ = ux_router
        monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
        # tanpa token -> 401 (belum login), tidak boleh eksekusi
        r = client.post("/ux/decide", json={"intent": "approve", "approver": "hacker"})
        assert r.status_code == 401

    def test_decide_uses_session_identity_when_enabled(self, ux_router, monkeypatch):
        ux_mod, client, users_file = ux_router
        monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
        # login -> token
        lr = client.post("/ux/login", json={"username": "van", "password": "pass-van"})
        assert lr.status_code == 200
        token = lr.json()["token"]
        me = client.get("/ux/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["user"]["username"] == "van"

        # submit mission sederhana (read-only web, cepat) supaya ada plan utk approve
        sub = client.post("/ux/submit", json={"text": "buka website example.com"})
        assert sub.status_code == 200
        mid = sub.json()["observability"]["mission_id"]
        # approve dengan token -> identitas sesi (van) dipakai, bukan body
        dec = client.post(
            "/ux/decide",
            json={"intent": "reject", "mission_id": mid, "approver": "bukan-saya"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dec.status_code == 200
        st = dec.json()
        # observability mencatat approver dari SESI (van), bukan body "bukan-saya"
        assert st["observability"]["approver"] == "van"

        # logout -> token invalid utk /me
        cl = client.post("/ux/logout", headers={"Authorization": f"Bearer {token}"})
        assert cl.status_code == 200
        me2 = client.get("/ux/me", headers={"Authorization": f"Bearer {token}"})
        assert me2.status_code == 401

    def test_viewer_role_denied_when_enabled(self, ux_router, monkeypatch):
        ux_mod, client, _ = ux_router
        monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
        lr = client.post("/ux/login", json={"username": "penonton", "password": "pass-view"})
        assert lr.status_code == 200
        token = lr.json()["token"]
        dec = client.post(
            "/ux/decide",
            json={"intent": "approve"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dec.status_code == 403  # role tidak berwenang

    def test_login_wrong_password(self, ux_router, monkeypatch):
        ux_mod, client, _ = ux_router
        monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
        r = client.post("/ux/login", json={"username": "van", "password": "salah"})
        assert r.status_code == 401

    def test_register_creates_and_autologin(self, ux_router, monkeypatch):
        """Register -> user baru dibuat + langsung dapat sesi (auto-login)."""
        ux_mod, client, users_file = ux_router
        monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
        r = client.post("/ux/register", json={"username": "budi", "password": "budi-rahasia"})
        assert r.status_code == 200
        body = r.json()
        assert body["created"] is True
        assert body["user"]["username"] == "budi"
        assert body["token"]
        # password tidak pernah dikembalikan
        assert "password" not in json.dumps(body).lower() or "budi-rahasia" not in json.dumps(body)
        # user langsung terverifikasi (siap login berikutnya)
        u = UserStore(path=str(users_file))
        assert u.verify("budi", "budi-rahasia")

    def test_register_duplicate_conflict(self, ux_router, monkeypatch):
        ux_mod, client, _ = ux_router
        monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
        r = client.post("/ux/register", json={"username": "van", "password": "pass-abcdef"})
        assert r.status_code == 409  # username sudah ada

    def test_register_short_password_400(self, ux_router, monkeypatch):
        ux_mod, client, _ = ux_router
        monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
        r = client.post("/ux/register", json={"username": "ciko", "password": "123"})
        assert r.status_code == 400

    def test_register_no_username_400(self, ux_router, monkeypatch):
        ux_mod, client, _ = ux_router
        monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
        r = client.post("/ux/register", json={"username": "", "password": "pass-abcdef"})
        assert r.status_code == 400

    def test_decide_non_auth_compat(self, ux_router, monkeypatch):
        """Mode AUTH nonaktif (default) -> approver body tetap dipakai (regresi M10)."""
        ux_mod, client, _ = ux_router
        monkeypatch.delenv("SAM_ENABLE_AUTH", raising=False)
        sub = client.post("/ux/submit", json={"text": "buka website example.com"})
        assert sub.status_code == 200
        mid = sub.json()["observability"]["mission_id"]
        dec = client.post(
            "/ux/decide", json={"intent": "reject", "mission_id": mid, "approver": "operator-b"}
        )
        assert dec.status_code == 200
        assert dec.json()["observability"]["approver"] == "operator-b"
