"""Sprint 106 — Runtime Security Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_security import (
    SecurityPolicy, AccessControl, AuditEntry, SecurityVerdict,
)
from sam.runtime_kernel.security_manager import SecurityManager
from sam.runtime_kernel.access_controller import AccessController
from sam.runtime_kernel.audit_logger import AuditLogger
from sam.runtime_kernel.verdict_engine import VerdictEngine
from sam.runtime_kernel.conversation_security import ConversationSecurity, DashboardSecurity
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestSecurityPolicy:
    def test_create(self):
        p = SecurityPolicy("p1", "RBAC", ["admin"], True)
        assert p.enabled

    def test_immutable(self):
        p = SecurityPolicy("p", "n")
        with pytest.raises(FrozenInstanceError):
            p.enabled = False


class TestAccessControl:
    def test_create(self):
        c = AccessControl("a1", "admin", "system", "write", True)
        assert c.granted

    def test_immutable(self):
        c = AccessControl("a", "s", "r")
        with pytest.raises(FrozenInstanceError):
            c.granted = True


class TestAuditEntry:
    def test_create(self):
        e = AuditEntry("e1", "login", "admin", "system", 100.0)
        assert e.action == "login"

    def test_immutable(self):
        e = AuditEntry("e", "action")
        with pytest.raises(FrozenInstanceError):
            e.action = "new"


class TestSecurityVerdict:
    def test_allowed(self):
        v = SecurityVerdict("v1", True, "ok")
        assert v.allowed

    def test_immutable(self):
        v = SecurityVerdict("v")
        with pytest.raises(FrozenInstanceError):
            v.allowed = True


# ============================================================
# 2. Engine Tests
# ============================================================

class TestSecurityManager:
    def test_add_policy(self):
        m = SecurityManager()
        m.add_policy(SecurityPolicy("p1", "RBAC"))
        assert m.count_policies() == 1

    def test_get_policy(self):
        m = SecurityManager()
        m.add_policy(SecurityPolicy("p1", "RBAC"))
        assert m.get_policy("p1") is not None
        assert m.get_policy("bogus") is None

    def test_check_access_allowed(self):
        m = SecurityManager()
        m.add_policy(SecurityPolicy("p1", "RBAC", ["admin:system"], True))
        v = m.check_access("v1", "admin", "system", "read")
        assert v.allowed

    def test_check_access_denied(self):
        m = SecurityManager()
        v = m.check_access("v1", "guest", "system", "write")
        assert not v.allowed

    def test_audit(self):
        m = SecurityManager()
        e = m.audit("e1", "login", "admin", "system", 100.0)
        assert m.count_audits() == 1
        assert e.action == "login"

    def test_get_audit_log(self):
        m = SecurityManager()
        m.audit("e1", "login")
        m.audit("e2", "logout")
        assert len(m.get_audit_log()) == 2


class TestAccessController:
    def test_add(self):
        c = AccessController()
        c.add(AccessControl("a1", "admin", "system", "write", True))
        assert c.count() == 1

    def test_get(self):
        c = AccessController()
        c.add(AccessControl("a1", "admin", "system", "write", True))
        assert c.get("a1") is not None
        assert c.get("bogus") is None

    def test_check_granted(self):
        c = AccessController()
        c.add(AccessControl("a1", "admin", "system", "write", True))
        assert c.check("admin", "system", "write")

    def test_check_denied(self):
        c = AccessController()
        assert not c.check("admin", "system", "write")

    def test_list_granted(self):
        c = AccessController()
        c.add(AccessControl("a1", "admin", "system", "read", True))
        c.add(AccessControl("a2", "admin", "config", "write", True))
        c.add(AccessControl("a3", "guest", "system", "read", False))
        granted = c.list_granted("admin")
        assert len(granted) == 2


class TestAuditLogger:
    def test_log(self):
        l = AuditLogger()
        l.log(AuditEntry("e1", "login"))
        assert l.count() == 1

    def test_get(self):
        l = AuditLogger()
        l.log(AuditEntry("e1", "login"))
        assert l.get("e1") is not None
        assert l.get("bogus") is None

    def test_find_by_subject(self):
        l = AuditLogger()
        l.log(AuditEntry("e1", "login", "admin"))
        l.log(AuditEntry("e2", "logout", "guest"))
        assert len(l.find_by_subject("admin")) == 1

    def test_find_by_action(self):
        l = AuditLogger()
        l.log(AuditEntry("e1", "login"))
        l.log(AuditEntry("e2", "login"))
        l.log(AuditEntry("e3", "logout"))
        assert len(l.find_by_action("login")) == 2

    def test_list_all(self):
        l = AuditLogger()
        l.log(AuditEntry("e1", "login"))
        assert len(l.list_all()) == 1


class TestVerdictEngine:
    def test_allow(self):
        v = VerdictEngine.allow("v1")
        assert v.allowed

    def test_deny(self):
        v = VerdictEngine.deny("v1")
        assert not v.allowed

    def test_is_allowed(self):
        v = VerdictEngine.allow("v1")
        assert VerdictEngine.is_allowed(v)
        assert not VerdictEngine.is_allowed(VerdictEngine.deny("v2"))


# ============================================================
# 3. Conversation Security
# ============================================================

class TestConversationSecurity:
    def test_queries(self):
        cs = ConversationSecurity(SecurityManager(), AccessController(),
                                  AuditLogger(), VerdictEngine())
        assert cs.get_manager() is not None
        assert cs.get_access_controller() is not None
        assert cs.get_audit_logger() is not None
        assert cs.get_verdict_engine() is not None
        layers = cs.describe_layers()
        assert len(layers) == 4
        assert cs.count_layers() == 4
        assert cs.get_policy_count() == 0
        assert cs.get_audit_count() == 0


# ============================================================
# 4. Dashboard Security
# ============================================================

class TestDashboardSecurity:
    def test_cards(self):
        ds = DashboardSecurity(SecurityManager(), AccessController(), AuditLogger())
        for card in [ds.engine_card(), ds.access_card(), ds.audit_card(),
                     ds.verdict_card(), ds.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        ds = DashboardSecurity(SecurityManager(), AccessController(), AuditLogger())
        for card in [ds.engine_card(), ds.access_card(), ds.audit_card(),
                     ds.verdict_card(), ds.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        SecurityPolicy("p", "n"),
        AccessControl("a", "s", "r"),
        AuditEntry("e", "action"),
        SecurityVerdict("v"),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, list(vars(obj).keys())[0], "x")


# ============================================================
# 6. Forbidden Imports
# ============================================================

class TestForbiddenImports:
    def test_0_forbidden_imports(self):
        import ast, pathlib
        forbidden = [
            "asyncio", "threading", "multiprocessing", "socket",
            "http", "urllib", "requests", "aiohttp",
            "subprocess", "os.system", "shutil",
            "sqlite3", "mysql", "postgresql",
            "redis", "celery", "rabbitmq", "kafka",
        ]
        src_dir = pathlib.Path("src/sam/runtime_kernel")
        if not src_dir.exists():
            pytest.skip("runtime_kernel dir not found")
        errors = []
        for f in sorted(src_dir.glob("*.py")):
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.split(".")[0]
                        if name in forbidden:
                            errors.append(f"{f.name}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        name = node.module.split(".")[0]
                        if name in forbidden:
                            errors.append(f"{f.name}: from {node.module}")
        assert not errors, f"Forbidden imports found: {errors}"


# ============================================================
# 7. Parametrized
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 31)))
def test_policy_parametrized(i):
    m = SecurityManager()
    m.add_policy(SecurityPolicy(f"p{i}", f"Policy {i}",
                               [f"rule{j}" for j in range(i % 4 + 1)], i % 2 == 0))
    assert m.count_policies() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_access_parametrized(i):
    c = AccessController()
    c.add(AccessControl(f"a{i}", f"user{i % 3}", f"res{i % 5}",
                        "read" if i % 2 == 0 else "write", i % 3 == 0))
    assert c.count() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_audit_parametrized(i):
    l = AuditLogger()
    actions = ["login", "logout", "access", "config"]
    l.log(AuditEntry(f"e{i}", actions[i % 4], f"user{i % 3}",
                    f"res{i}", float(i * 10)))
    assert l.count() == 1


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_verdict_parametrized(i):
    if i % 2 == 0:
        v = VerdictEngine.allow(f"v{i}", "allowed")
        assert v.allowed
    else:
        v = VerdictEngine.deny(f"v{i}", "denied")
        assert not v.allowed


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    cs = ConversationSecurity(SecurityManager(), AccessController(),
                              AuditLogger(), VerdictEngine())
    assert cs.count_layers() == 4


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    ds = DashboardSecurity(SecurityManager(), AccessController(), AuditLogger())
    c = ds.engine_card()
    assert c.status == "ready"
