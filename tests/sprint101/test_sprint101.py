"""Sprint 101 — Runtime Registry Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_registry import (
    RegistryEntry, CatalogEntry, LocatorResult,
    RuntimeDescriptor, RuntimeManifest,
)
from sam.runtime_kernel.runtime_catalog import RuntimeCatalog
from sam.runtime_kernel.runtime_locator import RuntimeLocator
from sam.runtime_kernel.runtime_descriptor import DescriptorEngine
from sam.runtime_kernel.runtime_manifest import ManifestEngine
from sam.runtime_kernel.conversation_registry import ConversationRegistry, DashboardRegistry
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestRegistryEntry:
    def test_create(self):
        e = RegistryEntry("e1", "guardian", "5.0.0")
        assert e.subsystem_name == "guardian"

    def test_immutable(self):
        e = RegistryEntry("e", "g", "v")
        with pytest.raises(FrozenInstanceError):
            e.status = "active"


class TestCatalogEntry:
    def test_create(self):
        e = CatalogEntry("c1", "Guardian", "runtime", "Guardian system", 3)
        assert e.entry_count == 3

    def test_immutable(self):
        e = CatalogEntry("c", "n", "cat")
        with pytest.raises(FrozenInstanceError):
            e.category = "new"


class TestLocatorResult:
    def test_found(self):
        r = LocatorResult("l1", "guardian", True, ["g1", "g2"])
        assert r.found
        assert len(r.entries) == 2

    def test_immutable(self):
        r = LocatorResult("l", "t")
        with pytest.raises(FrozenInstanceError):
            r.found = True


class TestRuntimeDescriptor:
    def test_create(self):
        d = RuntimeDescriptor("d1", "guardian", "live", ["observe", "decide"])
        assert "observe" in d.capabilities

    def test_immutable(self):
        d = RuntimeDescriptor("d", "g", "t")
        with pytest.raises(FrozenInstanceError):
            d.runtime_type = "new"


class TestRuntimeManifest:
    def test_create(self):
        m = RuntimeManifest("m1", "SAM", "9.11.0", {"guardian": "5.0.0"})
        assert m.dependencies["guardian"] == "5.0.0"

    def test_immutable(self):
        m = RuntimeManifest("m", "n", "v")
        with pytest.raises(FrozenInstanceError):
            m.version = "new"


# ============================================================
# 2. Engine Tests
# ============================================================

class TestRuntimeCatalog:
    def test_register(self):
        c = RuntimeCatalog()
        c.register(CatalogEntry("c1", "Guardian", "runtime"))
        assert c.count_entries() == 1

    def test_get(self):
        c = RuntimeCatalog()
        c.register(CatalogEntry("c1", "Guardian", "runtime"))
        assert c.get("c1") is not None
        assert c.get("bogus") is None

    def test_list_by_category(self):
        c = RuntimeCatalog()
        c.register(CatalogEntry("c1", "G", "runtime"))
        c.register(CatalogEntry("c2", "D", "decision"))
        assert len(c.list_by_category("runtime")) == 1
        assert len(c.list_by_category("decision")) == 1

    def test_list_all(self):
        c = RuntimeCatalog()
        c.register(CatalogEntry("c1", "G", "runtime"))
        assert len(c.list_all()) == 1


class TestRuntimeLocator:
    def test_register_target(self):
        l = RuntimeLocator()
        l.register_target("guardian", ["g1", "g2"])
        r = l.locate("l1", "guardian")
        assert r.found
        assert len(r.entries) == 2

    def test_not_found(self):
        l = RuntimeLocator()
        r = l.locate("l1", "bogus")
        assert not r.found

    def test_list_targets(self):
        l = RuntimeLocator()
        l.register_target("a", ["a1"])
        l.register_target("b", ["b1"])
        assert len(l.list_targets()) == 2


class TestDescriptorEngine:
    def test_create(self):
        e = DescriptorEngine()
        d = e.create("d1", "guardian", "live", ["observe"])
        assert len(d.capabilities) == 1
        assert e.count() == 1

    def test_get(self):
        e = DescriptorEngine()
        e.create("d1", "guardian", "live")
        assert e.get("d1") is not None
        assert e.get("bogus") is None


class TestManifestEngine:
    def test_create(self):
        e = ManifestEngine()
        m = e.create("m1", "SAM", "9.11.0", {"guardian": "5.0.0"})
        assert m.version == "9.11.0"
        assert e.count() == 1

    def test_get(self):
        e = ManifestEngine()
        e.create("m1", "SAM", "9.11.0")
        assert e.get("m1") is not None
        assert e.get("bogus") is None


# ============================================================
# 3. Conversation Registry
# ============================================================

class TestConversationRegistry:
    def test_queries(self):
        cr = ConversationRegistry(RuntimeCatalog(), RuntimeLocator(),
                                   DescriptorEngine(), ManifestEngine())
        assert cr.get_catalog() is not None
        assert cr.get_locator() is not None
        assert cr.get_descriptor_engine() is not None
        assert cr.get_manifest_engine() is not None
        comps = cr.describe_components()
        assert len(comps) == 4
        assert cr.count_components() == 4
        subs = cr.get_registered_subsystems()
        assert len(subs) == 6
        assert cr.count_subsystems() == 6


# ============================================================
# 4. Dashboard Registry
# ============================================================

class TestDashboardRegistry:
    def test_cards(self):
        dr = DashboardRegistry(RuntimeCatalog())
        for card in [dr.engine_card(), dr.catalog_card(), dr.descriptor_card(),
                     dr.manifest_card(), dr.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        dr = DashboardRegistry(RuntimeCatalog())
        for card in [dr.engine_card(), dr.catalog_card(), dr.descriptor_card(),
                     dr.manifest_card(), dr.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        RegistryEntry("e", "g", "v"),
        CatalogEntry("c", "n", "cat"),
        LocatorResult("l", "t"),
        RuntimeDescriptor("d", "g", "t"),
        RuntimeManifest("m", "n", "v"),
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

@pytest.mark.parametrize("i", list(range(1, 31)))
def test_catalog_parametrized(i):
    c = RuntimeCatalog()
    c.register(CatalogEntry(f"c{i}", f"Sub {i}", "runtime" if i % 2 == 0 else "decision"))
    assert c.count_entries() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_locator_parametrized(i):
    l = RuntimeLocator()
    l.register_target(f"target{i}", [f"e{j}" for j in range(i % 5)])
    r = l.locate(f"l{i}", f"target{i}")
    assert len(r.entries) == i % 5


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_descriptor_parametrized(i):
    e = DescriptorEngine()
    d = e.create(f"d{i}", f"sub{i}", "runtime", [f"cap{j}" for j in range(i % 4)])
    assert len(d.capabilities) == i % 4


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_manifest_parametrized(i):
    e = ManifestEngine()
    m = e.create(f"m{i}", f"Runtime {i}", f"{i}.0.0")
    assert m.version == f"{i}.0.0"


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    cr = ConversationRegistry(RuntimeCatalog(), RuntimeLocator(),
                               DescriptorEngine(), ManifestEngine())
    assert cr.count_subsystems() == 6


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    dr = DashboardRegistry(RuntimeCatalog())
    c = dr.engine_card()
    assert c.status == "ready"
    assert c.metrics["components"] == 4
