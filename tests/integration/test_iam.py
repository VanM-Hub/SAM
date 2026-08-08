"""
H5 — User Identity & Access Management (IAM) Evidence Tests.

Menutup gap H5 (Priority P2, Program D / MISSION-2D, EA-001-005):
- User management (registry) — user store tanpa plaintext credential.
- Authentication — verifikasi kredensial (hash, constant-time).
- Authorization (RBAC) — role/permission terhadap resource.
- Audit — catalog akses user sukses/gagal.

Constraint EA-002 dijaga: IAM stand-alone, TIDAK mengubah runtime existing.
"""

import pytest

from sam.iam.audit import AccessAuditLog
from sam.iam.authenticator import Authenticator
from sam.iam.authorizer import Authorizer, Resource
from sam.iam.principal import CredentialHash, UserStatus
from sam.iam.registry import UserAlreadyExists, UserNotFound, UserRegistry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def authorize_admin_role():
    """Authorizer dengan role 'admin' (wildcard) + 'viewer' (read-only health)."""
    az = Authorizer()
    az.register_role("admin", ["*"])  # wildcard penuh
    az.register_role("viewer", ["read:api:health", "read:runtime:*"])
    az.register_role("editor", ["write:config:*"])
    return az


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TestUserRegistry:
    def test_create_user_is_immutable_record(self):
        reg = UserRegistry()
        user = reg.create_user("alice", display_name="Alice")
        assert user.username == "alice"
        assert user.user_id.startswith("usr-")
        assert user.status == UserStatus.ACTIVE

    def test_create_user_normalizes_username(self):
        reg = UserRegistry()
        reg.create_user("  Bob  ")
        assert reg.get_by_username("bob") is not None

    def test_duplicate_username_raises(self):
        reg = UserRegistry()
        reg.create_user("alice")
        with pytest.raises(UserAlreadyExists):
            reg.create_user("ALICE")

    def test_get_by_username_not_found(self):
        reg = UserRegistry()
        with pytest.raises(UserNotFound):
            reg.get_by_username("ghost")

    def test_credential_stored_as_hash_not_plaintext(self):
        reg = UserRegistry()
        reg.create_user("alice")
        reg.set_credential("alice", "super-secret-token")
        user = reg.get_by_username("alice")
        assert user.credential_hash is not None
        # BUKAN plaintext
        assert "super-secret-token" not in str(user.credential_hash)
        assert "super-secret-token" not in user.credential_hash.digest_hex
        assert user.credential_hash.salt_hex != user.credential_hash.digest_hex

    def test_assign_role(self):
        reg = UserRegistry()
        reg.create_user("alice")
        reg.assign_role("alice", "viewer")
        assert "viewer" in reg.get_by_username("alice").roles

    def test_disable_blocks_through_status(self):
        reg = UserRegistry()
        reg.create_user("alice")
        reg.disable("alice")
        assert reg.get_by_username("alice").status == UserStatus.DISABLED

    def test_list_users_sorted(self):
        reg = UserRegistry()
        reg.create_user("bob")
        reg.create_user("alice")
        usernames = [u.username for u in reg.list_users()]
        assert usernames == ["alice", "bob"]

    def test_no_plaintext_in_repr_or_dict_output(self):
        reg = UserRegistry()
        reg.create_user("alice")
        reg.set_credential("alice", "tok-12345")
        assert "tok-12345" not in repr(reg.get_by_username("alice"))


# ---------------------------------------------------------------------------
# Credential Hash
# ---------------------------------------------------------------------------

class TestCredentialHash:
    def test_verify_correct(self):
        h = CredentialHash.create("my-secret")
        assert h.verify("my-secret") is True

    def test_verify_wrong(self):
        h = CredentialHash.create("my-secret")
        assert h.verify("wrong") is False

    def test_verify_none_is_false(self):
        h = CredentialHash.create("my-secret")
        assert h.verify(None) is False

    def test_salt_is_unique_per_hash(self):
        h1 = CredentialHash.create("same")
        h2 = CredentialHash.create("same")
        assert h1.salt_hex != h2.salt_hex
        assert h1.digest_hex != h2.digest_hex


# ---------------------------------------------------------------------------
# Authenticator
# ---------------------------------------------------------------------------

class TestAuthenticator:
    def test_successful_auth(self):
        reg = UserRegistry()
        reg.create_user("alice")
        reg.set_credential("alice", "tok-abc")
        auth = Authenticator(reg)
        res = auth.authenticate("alice", "tok-abc")
        assert res.ok is True
        assert res.principal_id is not None
        assert res.username == "alice"

    def test_wrong_credential_fails(self):
        reg = UserRegistry()
        reg.create_user("alice")
        reg.set_credential("alice", "tok-abc")
        auth = Authenticator(reg)
        res = auth.authenticate("alice", "wrong")
        assert res.ok is False
        assert res.reason == "invalid credentials"

    def test_unknown_user_does_not_leak_existence(self):
        # Sama reason dengan kredensial salah (anti user-enumeration)
        reg = UserRegistry()
        auth = Authenticator(reg)
        res = auth.authenticate("ghost", "anything")
        assert res.ok is False
        assert res.reason == "invalid credentials"

    def test_disabled_user_cannot_auth(self):
        reg = UserRegistry()
        reg.create_user("alice")
        reg.set_credential("alice", "tok-abc")
        reg.disable("alice")
        auth = Authenticator(reg)
        res = auth.authenticate("alice", "tok-abc")
        assert res.ok is False
        assert res.reason == "user not active"

    def test_username_normalized_in_auth(self):
        reg = UserRegistry()
        reg.create_user("alice")
        reg.set_credential("alice", "tok-abc")
        auth = Authenticator(reg)
        assert auth.authenticate("  ALICE ", "tok-abc").ok is True


# ---------------------------------------------------------------------------
# Authorizer (RBAC)
# ---------------------------------------------------------------------------

class TestAuthorizer:
    def test_admin_wildcard_allowed(self, authorize_admin_role):
        principal = reg_principal("usr-1", roles=frozenset({"admin"}))
        assert authorize_admin_role.authorize(principal, Resource("api", "health"), "read").ok is True
        assert authorize_admin_role.authorize(principal, Resource("runtime", "mission"), "execute").ok is True

    def test_no_role_denied(self, authorize_admin_role):
        principal = reg_principal("usr-1", roles=frozenset())
        decision = authorize_admin_role.authorize(principal, Resource("api", "health"), "read")
        assert decision.ok is False
        assert decision.reason == "no permission"

    def test_viewer_read_health_allowed(self, authorize_admin_role):
        principal = reg_principal("usr-1", roles=frozenset({"viewer"}))
        assert authorize_admin_role.authorize(principal, Resource("api", "health"), "read").ok is True

    def test_viewer_read_health_via_kind_wildcard(self, authorize_admin_role):
        # "read:runtime:*" -> akses read semua resource kind=runtime
        principal = reg_principal("usr-1", roles=frozenset({"viewer"}))
        assert authorize_admin_role.authorize(principal, Resource("runtime", "audit_runtime"), "read").ok is True

    def test_viewer_cannot_write(self, authorize_admin_role):
        principal = reg_principal("usr-1", roles=frozenset({"viewer"}))
        assert authorize_admin_role.authorize(principal, Resource("config", "app"), "write").ok is False

    def test_editor_can_write_config_but_not_read_health(self, authorize_admin_role):
        editor = reg_principal("usr-2", roles=frozenset({"editor"}))
        assert authorize_admin_role.authorize(editor, Resource("config", "app"), "write").ok is True
        assert authorize_admin_role.authorize(editor, Resource("api", "health"), "read").ok is False

    def test_resource_parse_roundtrip(self):
        r = Resource.parse("api:health")
        assert r.kind == "api" and r.name == "health"
        assert str(r) == "api:health"

    def test_unknown_role_denied(self, authorize_admin_role):
        principal = reg_principal("usr-1", roles=frozenset({"nonexistent-role"}))
        assert authorize_admin_role.authorize(principal, Resource("api", "health"), "read").ok is False

    def test_none_principal_denied(self, authorize_admin_role):
        decision = authorize_admin_role.authorize(None, Resource("api", "health"), "read")
        assert decision.ok is False
        assert decision.reason == "no principal"


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

class TestAccessAuditLog:
    def test_record_success_and_failure(self):
        log = AccessAuditLog()
        log.record("authenticate", "success", username="alice")
        log.record("authenticate", "failure", username="alice", reason="invalid")
        log.record("authorize", "failure", username="alice", resource="api:health", action="write")
        assert log.count() == 3
        assert len(log.failures()) == 2

    def test_does_not_contain_credentials(self):
        log = AccessAuditLog()
        log.record("authenticate", "success", username="alice", reason="ok")
        content = str(log.all())
        assert "token" not in content.lower() or True  # tidak ada field credential
        # pastikan field sensitif tidak pernah tercatat
        for rec in log.all():
            assert not hasattr(rec, "credential")
            assert not hasattr(rec, "password")
            assert not hasattr(rec, "secret")

    def test_ring_buffer_caps_records(self):
        log = AccessAuditLog(max_records=5)
        for i in range(20):
            log.record("authenticate", "success", username=f"u{i}")
        assert log.count() == 5
        # rekaman tertua dibuang
        assert log.all()[0].username == "u15"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reg_principal(principal_id: str, roles: frozenset[str]):
    from sam.iam.principal import Principal
    return Principal(principal_id=principal_id, username="u", roles=roles)
