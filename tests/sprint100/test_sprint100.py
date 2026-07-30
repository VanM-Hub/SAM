"""Sprint 100 — Runtime Context Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_context import (
    RuntimeContext, RuntimeIdentity, RuntimeEnvironment,
    RuntimeProfile, RuntimeConfiguration,
)
from sam.runtime_kernel.runtime_identity import IdentityBuilder, EnvironmentBuilder
from sam.runtime_kernel.runtime_environment import EnvironmentEngine
from sam.runtime_kernel.runtime_profile import ProfileEngine
from sam.runtime_kernel.runtime_configuration import ConfigurationEngine
from sam.runtime_kernel.conversation_runtime_context import (
    ConversationRuntimeContext, DashboardRuntimeContext,
)
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestRuntimeContext:
    def test_create(self):
        c = RuntimeContext("r1", "SAM", "9.11.0", "Main runtime")
        assert c.runtime_id == "r1"
        assert c.version == "9.11.0"

    def test_immutable(self):
        c = RuntimeContext("r1", "n", "v")
        with pytest.raises(FrozenInstanceError):
            c.name = "new"


class TestRuntimeIdentity:
    def test_create(self):
        i = RuntimeIdentity("i1", "host1", "inst1")
        assert i.hostname == "host1"

    def test_immutable(self):
        i = RuntimeIdentity("i", "h", "inst")
        with pytest.raises(FrozenInstanceError):
            i.hostname = "new"


class TestRuntimeEnvironment:
    def test_create(self):
        e = RuntimeEnvironment("e1", "production", features=["observe", "decide"])
        assert e.environment_type == "production"
        assert "observe" in e.features

    def test_immutable(self):
        e = RuntimeEnvironment("e", "dev")
        with pytest.raises(FrozenInstanceError):
            e.environment_type = "prod"


class TestRuntimeProfile:
    def test_create(self):
        p = RuntimeProfile("p1", "default", mode="safe")
        assert p.mode == "safe"

    def test_immutable(self):
        p = RuntimeProfile("p", "n")
        with pytest.raises(FrozenInstanceError):
            p.mode = "new"


class TestRuntimeConfiguration:
    def test_create(self):
        c = RuntimeConfiguration("c1", settings={"timeout": 60}, timeout_seconds=60.0)
        assert c.settings["timeout"] == 60

    def test_immutable(self):
        c = RuntimeConfiguration("c")
        with pytest.raises(FrozenInstanceError):
            c.enabled = False


# ============================================================
# 2. Identity / Environment / Profile / Config Engine Tests
# ============================================================

class TestIdentityBuilder:
    def test_build(self):
        b = IdentityBuilder()
        i = b.build("i1", "srv01", "prod-instance", "production")
        assert i.instance_type == "production"


class TestEnvironmentBuilder:
    def test_build(self):
        b = EnvironmentBuilder()
        e = b.build("e1", "staging")
        assert e.environment_type == "staging"


class TestEnvironmentEngine:
    def test_profile(self):
        e = EnvironmentEngine()
        p = e.create_profile("p1", "default", "safe")
        assert p.mode == "safe"

    def test_config(self):
        e = EnvironmentEngine()
        c = e.create_config("c1")
        assert c.enabled

    def test_feature_check(self):
        e = EnvironmentEngine()
        env = RuntimeEnvironment("e1", "dev", features=["a", "b"])
        assert e.feature_check(env, "a")
        assert not e.feature_check(env, "z")

    def test_profile_cap(self):
        e = EnvironmentEngine()
        p = RuntimeProfile("p1", "default", capabilities=["observe"])
        assert e.profile_has_capability(p, "observe")
        assert not e.profile_has_capability(p, "decide")


class TestProfileEngine:
    def test_build(self):
        e = ProfileEngine()
        p = e.build_profile("p1", "dev", "normal", ["observe"])
        assert "observe" in p.capabilities

    def test_add_defaults(self):
        e = ProfileEngine()
        p = RuntimeProfile("p1", "dev", capabilities=[])
        p2 = e.add_defaults(p)
        assert "observe" in p2.capabilities
        assert "act" in p2.capabilities


class TestConfigurationEngine:
    def test_create(self):
        e = ConfigurationEngine()
        c = e.create("c1", {"a": 1})
        assert c.settings["a"] == 1

    def test_merge(self):
        e = ConfigurationEngine()
        c = e.create("c1", {"a": 1, "b": 2})
        c2 = e.merge(c, {"b": 3, "c": 4})
        assert c2.settings["a"] == 1
        assert c2.settings["b"] == 3
        assert c2.settings["c"] == 4

    def test_has_setting(self):
        e = ConfigurationEngine()
        c = e.create("c1", {"x": 1})
        assert e.has_setting(c, "x")
        assert not e.has_setting(c, "y")

    def test_get_setting(self):
        e = ConfigurationEngine()
        c = e.create("c1", {"x": 42})
        assert e.get_setting(c, "x") == 42
        assert e.get_setting(c, "missing", "def") == "def"


# ============================================================
# 3. Conversation Context Bridge
# ============================================================

class TestConversationRuntimeContext:
    def test_queries(self):
        cr = ConversationRuntimeContext(
            ConfigurationEngine(), IdentityBuilder(), EnvironmentBuilder()
        )
        assert cr.get_config_engine() is not None
        assert cr.get_identity_builder() is not None
        assert cr.get_env_builder() is not None
        layers = cr.describe_layers()
        assert len(layers) == 4
        assert cr.count_layers() == 4
        settings = cr.get_setting_names()
        assert len(settings) == 5
        assert cr.count_settings() == 5
        assert cr.has_profile_caps()


# ============================================================
# 4. Dashboard Context Bridge
# ============================================================

class TestDashboardRuntimeContext:
    def test_cards(self):
        dc = DashboardRuntimeContext(ConfigurationEngine())
        for card in [dc.engine_card(), dc.identity_card(), dc.environment_card(),
                     dc.configuration_card(), dc.summary_card()]:
            assert card.status == "ready"
            assert len(card.items) >= 1

    def test_all_frozen(self):
        dc = DashboardRuntimeContext(ConfigurationEngine())
        for card in [dc.engine_card(), dc.identity_card(), dc.environment_card(),
                     dc.configuration_card(), dc.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        RuntimeContext("r", "n", "v"),
        RuntimeIdentity("i", "h", "inst"),
        RuntimeEnvironment("e", "dev"),
        RuntimeProfile("p", "n"),
        RuntimeConfiguration("c"),
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
# 7. Parametrized Tests
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 36)))
def test_identity_parametrized(i):
    b = IdentityBuilder()
    i_obj = b.build(f"id{i}", f"host{i}", f"inst{i}", "production" if i % 2 == 0 else "dev")
    assert i_obj.hostname == f"host{i}"


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_env_parametrized(i):
    e = EnvironmentEngine()
    p = e.create_profile(f"p{i}", f"Profile {i}", "safe" if i % 3 == 0 else "normal")
    assert p.profile_id == f"p{i}"


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_config_parametrized(i):
    e = ConfigurationEngine()
    c = e.create(f"c{i}", {"timeout": i * 10}, timeout=float(i * 5))
    assert c.settings["timeout"] == i * 10
    assert c.timeout_seconds == float(i * 5)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_profile_parametrized(i):
    e = ProfileEngine()
    p = e.build_profile(f"p{i}", f"Profile {i}", capabilities=[f"cap{j}" for j in range(i % 4)])
    assert len(p.capabilities) == i % 4


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    cr = ConversationRuntimeContext(ConfigurationEngine(), IdentityBuilder(), EnvironmentBuilder())
    assert cr.count_layers() == 4


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    dc = DashboardRuntimeContext(ConfigurationEngine())
    c = dc.engine_card()
    assert isinstance(c, ExecutionCard)
    assert c.status == "ready"
