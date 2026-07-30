"""Sprint 111 — Runtime Kernel Final Assembly Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.kernel_final import (
    KernelFinalReport, ComponentHealth, KernelSummary, FinalVerdict,
)
from sam.runtime_kernel.final_inspector import FinalInspector
from sam.runtime_kernel.kernel_reporter import KernelReporter
from sam.runtime_kernel.conversation_final import ConversationFinal, DashboardFinal
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestKernelFinalReport:
    def test_create(self):
        r = KernelFinalReport("r1", "10.0.0", "complete",
                             ["context", "registry"], {"total": 2})
        assert r.status == "complete"

    def test_immutable(self):
        r = KernelFinalReport("r", "v")
        with pytest.raises(FrozenInstanceError):
            r.status = "complete"


class TestComponentHealth:
    def test_healthy(self):
        c = ComponentHealth("context", True, "ok")
        assert c.healthy

    def test_immutable(self):
        c = ComponentHealth("c")
        with pytest.raises(FrozenInstanceError):
            c.healthy = False


class TestKernelSummary:
    def test_create(self):
        s = KernelSummary("ks1", 11, 11, "10.0.0")
        assert s.healthy_count == 11

    def test_immutable(self):
        s = KernelSummary("ks")
        with pytest.raises(FrozenInstanceError):
            s.healthy_count = 5


class TestFinalVerdict:
    def test_ready(self):
        v = FinalVerdict("v1", True, "all ok")
        assert v.ready

    def test_immutable(self):
        v = FinalVerdict("v")
        with pytest.raises(FrozenInstanceError):
            v.ready = True


# ============================================================
# 2. Engine Tests
# ============================================================

class TestFinalInspector:
    def test_count(self):
        i = FinalInspector()
        assert i.count_components() == 11

    def test_list(self):
        i = FinalInspector()
        items = i.list_components()
        assert "context" in items
        assert "telemetry" in items

    def test_inspect(self):
        i = FinalInspector()
        components = i.inspect_components()
        assert len(components) == 11
        assert all(c.healthy for c in components)

    def test_generate_summary(self):
        i = FinalInspector()
        s = i.generate_summary()
        assert s.total_components == 11
        assert s.healthy_count == 11
        assert s.version == "10.0.0-alpha.111"

    def test_final_verdict_ready(self):
        i = FinalInspector()
        v = i.final_verdict("v1")
        assert v.ready
        assert "healthy" in v.reason


class TestKernelReporter:
    def test_generate(self):
        r = KernelReporter()
        report = r.generate_final_report("r1", "10.0.0",
                                         ["context", "registry"],
                                         {"components": 2})
        assert report.status == "complete"
        assert len(report.components) == 2

    def test_count(self):
        r = KernelReporter()
        assert r.count([KernelFinalReport("r1", "v")]) == 1


# ============================================================
# 3. Conversation Final
# ============================================================

class TestConversationFinal:
    def test_queries(self):
        cf = ConversationFinal(FinalInspector(), KernelReporter())
        assert cf.get_inspector() is not None
        assert cf.get_reporter() is not None
        layers = cf.describe_layers()
        assert len(layers) == 2
        assert cf.count_layers() == 2
        assert cf.get_component_count() == 11
        assert cf.get_status() == "ready"

    def test_list_components(self):
        cf = ConversationFinal(FinalInspector(), KernelReporter())
        items = cf.list_components()
        assert len(items) == 11
        assert cf.count_components_list() == 11


# ============================================================
# 4. Dashboard Final
# ============================================================

class TestDashboardFinal:
    def test_cards(self):
        df = DashboardFinal(FinalInspector(), KernelReporter())
        for card in [df.engine_card(), df.inspector_card(), df.report_card(),
                     df.summary_card(), df.verdict_card()]:
            assert len(card.metrics) >= 1

    def test_engine_status(self):
        df = DashboardFinal(FinalInspector(), KernelReporter())
        c = df.engine_card()
        assert c.status == "ready"
        assert c.metrics["components"] == 11

    def test_verdict_ready(self):
        df = DashboardFinal(FinalInspector(), KernelReporter())
        c = df.verdict_card()
        assert c.metrics["ready"] == 1

    def test_summary_card(self):
        df = DashboardFinal(FinalInspector(), KernelReporter())
        c = df.summary_card()
        assert "10.0.0" in c.description

    def test_all_frozen(self):
        df = DashboardFinal(FinalInspector(), KernelReporter())
        for card in [df.engine_card(), df.inspector_card(), df.report_card(),
                     df.summary_card(), df.verdict_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        KernelFinalReport("r", "v"),
        ComponentHealth("c"),
        KernelSummary("ks"),
        FinalVerdict("v"),
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

@pytest.mark.parametrize("i", list(range(1, 36)))
def test_component_parametrized(i):
    i_obj = FinalInspector()
    assert i_obj.count_components() == 11


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_report_parametrized(i):
    r = KernelReporter()
    components = [f"comp{j}" for j in range(i % 7)]
    report = r.generate_final_report(f"r{i}", f"{i}.0.0", components)
    assert len(report.components) == i % 7


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_verdict_parametrized(i):
    i_obj = FinalInspector()
    v = i_obj.final_verdict(f"v{i}")
    assert v.ready


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_components_parametrized(i):
    i_obj = FinalInspector()
    comps = i_obj.inspect_components()
    assert comps[i % 11].healthy


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    cf = ConversationFinal(FinalInspector(), KernelReporter())
    assert cf.count_layers() == 2


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    df = DashboardFinal(FinalInspector(), KernelReporter())
    c = df.engine_card()
    assert c.metrics["components"] == 11
