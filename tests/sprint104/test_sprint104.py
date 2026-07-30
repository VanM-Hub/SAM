"""Sprint 104 — Runtime Bridge Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_adapter import (
    SubsystemAdapter, BridgeRoute, TransformRule, ProtocolMap, InteropResult,
)
from sam.runtime_kernel.adapter_registry import AdapterRegistry
from sam.runtime_kernel.bridge_router import BridgeRouter
from sam.runtime_kernel.transform_engine import TransformEngine
from sam.runtime_kernel.protocol_mapper import ProtocolMapper
from sam.runtime_kernel.conversation_bridge import ConversationBridge, DashboardBridge
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestSubsystemAdapter:
    def test_create(self):
        a = SubsystemAdapter("a1", "guardian", "json", "internal",
                            {"field": "target"})
        assert a.subsystem_name == "guardian"

    def test_immutable(self):
        a = SubsystemAdapter("a", "g")
        with pytest.raises(FrozenInstanceError):
            a.subsystem_name = "new"


class TestBridgeRoute:
    def test_create(self):
        r = BridgeRoute("r1", "kernel", "guardian")
        assert r.active

    def test_immutable(self):
        r = BridgeRoute("r")
        with pytest.raises(FrozenInstanceError):
            r.active = False


class TestTransformRule:
    def test_create(self):
        r = TransformRule("r1", "name", "Name", "upper")
        assert r.transform_type == "upper"

    def test_immutable(self):
        r = TransformRule("r")
        with pytest.raises(FrozenInstanceError):
            r.transform_type = "lower"


class TestProtocolMap:
    def test_create(self):
        p = ProtocolMap("p1", "internal", "guardian", "1.0")
        assert p.protocol == "internal"

    def test_immutable(self):
        p = ProtocolMap("p")
        with pytest.raises(FrozenInstanceError):
            p.protocol = "external"


class TestInteropResult:
    def test_compatible(self):
        r = InteropResult("r1", True)
        assert r.compatible

    def test_immutable(self):
        r = InteropResult("r")
        with pytest.raises(FrozenInstanceError):
            r.compatible = True


# ============================================================
# 2. Engine Tests
# ============================================================

class TestAdapterRegistry:
    def test_register(self):
        r = AdapterRegistry()
        r.register(SubsystemAdapter("a1", "guardian"))
        assert r.count() == 1

    def test_get(self):
        r = AdapterRegistry()
        r.register(SubsystemAdapter("a1", "guardian"))
        assert r.get("a1") is not None
        assert r.get("bogus") is None

    def test_list_all(self):
        r = AdapterRegistry()
        r.register(SubsystemAdapter("a1", "guardian"))
        r.register(SubsystemAdapter("a2", "decision"))
        assert len(r.list_all()) == 2

    def test_find_by_subsystem(self):
        r = AdapterRegistry()
        r.register(SubsystemAdapter("a1", "guardian"))
        r.register(SubsystemAdapter("a2", "decision"))
        r.register(SubsystemAdapter("a3", "guardian"))
        assert len(r.find_by_subsystem("guardian")) == 2


class TestBridgeRouter:
    def test_add(self):
        r = BridgeRouter()
        r.add(BridgeRoute("r1", "kernel", "guardian"))
        assert r.count() == 1

    def test_get(self):
        r = BridgeRouter()
        r.add(BridgeRoute("r1", "kernel", "guardian"))
        assert r.get("r1") is not None
        assert r.get("bogus") is None

    def test_deactivate(self):
        r = BridgeRouter()
        r.add(BridgeRoute("r1", "kernel", "guardian"))
        r2 = r.deactivate("r1")
        assert r2 is not None
        assert not r2.active
        assert not r.list_active()

    def test_list_active(self):
        r = BridgeRouter()
        r.add(BridgeRoute("r1", "a", "b"))
        r.add(BridgeRoute("r2", "c", "d"))
        assert len(r.list_active()) == 2
        r.deactivate("r1")
        assert len(r.list_active()) == 1


class TestTransformEngine:
    def test_add_rule(self):
        e = TransformEngine()
        e.add_rule(TransformRule("r1", "name", "Name", "upper"))
        assert e.count() == 1

    def test_get_rule(self):
        e = TransformEngine()
        e.add_rule(TransformRule("r1"))
        assert e.get_rule("r1") is not None
        assert e.get_rule("bogus") is None

    def test_apply_upper(self):
        e = TransformEngine()
        e.add_rule(TransformRule("r1", "name", "Name", "upper"))
        assert e.apply("r1", "hello") == "HELLO"

    def test_apply_lower(self):
        e = TransformEngine()
        e.add_rule(TransformRule("r1", "name", "Name", "lower"))
        assert e.apply("r1", "HELLO") == "hello"

    def test_apply_prefix(self):
        e = TransformEngine()
        e.add_rule(TransformRule("r1", "name", "Name", "prefix"))
        assert e.apply("r1", "test") == "sam_test"

    def test_apply_missing(self):
        e = TransformEngine()
        assert e.apply("bogus", "val") == "val"

    def test_apply_direct(self):
        e = TransformEngine()
        e.add_rule(TransformRule("r1", "name", "Name", "direct"))
        assert e.apply("r1", "test") == "test"


class TestProtocolMapper:
    def test_register(self):
        m = ProtocolMapper()
        m.register(ProtocolMap("p1", "internal", "guardian"))
        assert m.count() == 1

    def test_get(self):
        m = ProtocolMapper()
        m.register(ProtocolMap("p1", "internal", "guardian"))
        assert m.get("p1") is not None
        assert m.get("bogus") is None

    def test_check_interop_compatible(self):
        m = ProtocolMapper()
        a = ProtocolMap("p1", "internal", "guardian", "1.0")
        b = ProtocolMap("p2", "internal", "decision", "1.0")
        r = m.check_interop("r1", a, b)
        assert r.compatible

    def test_check_interop_mismatch_protocol(self):
        m = ProtocolMapper()
        a = ProtocolMap("p1", "internal", "guardian", "1.0")
        b = ProtocolMap("p2", "external", "decision", "1.0")
        r = m.check_interop("r1", a, b)
        assert not r.compatible
        assert len(r.messages) >= 1

    def test_check_interop_mismatch_version(self):
        m = ProtocolMapper()
        a = ProtocolMap("p1", "internal", "guardian", "1.0")
        b = ProtocolMap("p2", "internal", "decision", "2.0")
        r = m.check_interop("r1", a, b)
        assert not r.compatible
        assert len(r.messages) >= 1


# ============================================================
# 3. Conversation Bridge
# ============================================================

class TestConversationBridge:
    def test_queries(self):
        cb = ConversationBridge(AdapterRegistry(), BridgeRouter(),
                                TransformEngine(), ProtocolMapper())
        assert cb.get_adapter_registry() is not None
        assert cb.get_bridge_router() is not None
        assert cb.get_transform_engine() is not None
        assert cb.get_protocol_mapper() is not None
        layers = cb.describe_layers()
        assert len(layers) == 4
        assert cb.count_layers() == 4
        subs = cb.get_registered_subsystems()
        assert "none" in subs
        assert cb.count_adapters() == 0


# ============================================================
# 4. Dashboard Bridge
# ============================================================

class TestDashboardBridge:
    def test_cards(self):
        db = DashboardBridge(AdapterRegistry(), BridgeRouter(),
                             TransformEngine(), ProtocolMapper())
        for card in [db.engine_card(), db.adapter_card(), db.router_card(),
                     db.transform_card(), db.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        db = DashboardBridge(AdapterRegistry(), BridgeRouter(),
                             TransformEngine(), ProtocolMapper())
        for card in [db.engine_card(), db.adapter_card(), db.router_card(),
                     db.transform_card(), db.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        SubsystemAdapter("a", "g"),
        BridgeRoute("r"),
        TransformRule("r"),
        ProtocolMap("p"),
        InteropResult("r"),
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
def test_adapter_parametrized(i):
    r = AdapterRegistry()
    r.register(SubsystemAdapter(f"a{i}", f"sub{i}", "json", "internal",
                               {f"f{j}": f"t{j}" for j in range(i % 4)}))
    assert r.count() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_route_parametrized(i):
    r = BridgeRouter()
    r.add(BridgeRoute(f"r{i}", f"src{i}", f"tgt{i}", i % 2 == 0))
    assert r.count() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_transform_parametrized(i):
    e = TransformEngine()
    types = ["upper", "lower", "prefix"]
    e.add_rule(TransformRule(f"r{i}", "f", "t", types[i % 3]))
    val = "Test" if i % 2 == 0 else "hello"
    result = e.apply(f"r{i}", val)
    assert isinstance(result, str)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_protocol_parametrized(i):
    m = ProtocolMapper()
    m.register(ProtocolMap(f"p{i}", "internal" if i % 2 == 0 else "external",
                          f"sub{i}", f"{i % 5 + 1}.0"))
    assert m.count() == 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_interop_parametrized(i):
    m = ProtocolMapper()
    a = ProtocolMap("p1", "internal", "g", "1.0")
    b = ProtocolMap("p2", "internal" if i % 2 == 0 else "external", "d", "1.0")
    r = m.check_interop(f"r{i}", a, b)
    assert r.compatible == (i % 2 == 0)


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    cb = ConversationBridge(AdapterRegistry(), BridgeRouter(),
                            TransformEngine(), ProtocolMapper())
    assert cb.count_layers() == 4


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_dashboard_parametrized(i):
    db = DashboardBridge(AdapterRegistry(), BridgeRouter(),
                         TransformEngine(), ProtocolMapper())
    c = db.engine_card()
    assert c.status == "ready"
