"""Sprint 110 — Runtime Telemetry Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_telemetry import (
    TelemetryMetric, TelemetrySample, MetricSummary, TelemetryReport,
)
from sam.runtime_kernel.telemetry_collector import TelemetryCollector
from sam.runtime_kernel.metrics_aggregator import MetricsAggregator
from sam.runtime_kernel.telemetry_reporter import TelemetryReporter
from sam.runtime_kernel.conversation_telemetry import ConversationTelemetry, DashboardTelemetry
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestTelemetryMetric:
    def test_create(self):
        m = TelemetryMetric("m1", "cpu", 45.0, "%", "kernel")
        assert m.value == 45.0

    def test_immutable(self):
        m = TelemetryMetric("m", "cpu")
        with pytest.raises(FrozenInstanceError):
            m.value = 50.0


class TestTelemetrySample:
    def test_create(self):
        s = TelemetrySample("s1", timestamp=100.0)
        assert s.timestamp == 100.0

    def test_immutable(self):
        s = TelemetrySample("s")
        with pytest.raises(FrozenInstanceError):
            s.timestamp = 50.0


class TestMetricSummary:
    def test_create(self):
        s = MetricSummary("sum1", "cpu", 45.0, 10.0, 90.0, 5)
        assert s.avg == 45.0

    def test_immutable(self):
        s = MetricSummary("s", "cpu")
        with pytest.raises(FrozenInstanceError):
            s.avg = 50.0


class TestTelemetryReport:
    def test_create(self):
        r = TelemetryReport("r1", 100.0, total_metrics=5)
        assert r.total_metrics == 5

    def test_immutable(self):
        r = TelemetryReport("r", 0.0)
        with pytest.raises(FrozenInstanceError):
            r.total_metrics = 10


# ============================================================
# 2. Engine Tests
# ============================================================

class TestTelemetryCollector:
    def test_record_metric(self):
        c = TelemetryCollector()
        c.record_metric(TelemetryMetric("m1", "cpu", 45.0))
        assert c.count_metrics() == 1

    def test_create_sample(self):
        c = TelemetryCollector()
        s = c.create_sample("s1", 100.0)
        assert c.count_samples() == 1

    def test_get_sample(self):
        c = TelemetryCollector()
        c.create_sample("s1", 100.0)
        assert c.get_sample("s1") is not None
        assert c.get_sample("bogus") is None

    def test_get_all_metrics(self):
        c = TelemetryCollector()
        c.record_metric(TelemetryMetric("m1", "cpu", 45.0))
        c.record_metric(TelemetryMetric("m2", "mem", 60.0))
        assert len(c.get_all_metrics()) == 2

    def test_sample_with_metrics(self):
        c = TelemetryCollector()
        metrics = [TelemetryMetric("m1", "cpu", 45.0),
                   TelemetryMetric("m2", "mem", 60.0)]
        c.create_sample("s1", 100.0, metrics)
        assert c.count_metrics() == 0  # metrics recorded via create_sample, not record_metric
        s = c.get_sample("s1")
        assert s is not None
        assert len(s.metrics) == 2


class TestMetricsAggregator:
    def test_summarize(self):
        a = MetricsAggregator()
        metrics = [
            TelemetryMetric("m1", "cpu", 10.0),
            TelemetryMetric("m2", "cpu", 30.0),
            TelemetryMetric("m3", "cpu", 50.0),
        ]
        s = a.summarize("cpu", metrics)
        assert s.avg == 30.0
        assert s.min == 10.0
        assert s.max == 50.0
        assert s.count == 3

    def test_summarize_empty(self):
        a = MetricsAggregator()
        s = a.summarize("cpu", [])
        assert s.count == 0

    def test_group_by_subsystem(self):
        a = MetricsAggregator()
        metrics = [
            TelemetryMetric("m1", "cpu", 10.0, subsystem="kernel"),
            TelemetryMetric("m2", "mem", 20.0, subsystem="kernel"),
            TelemetryMetric("m3", "cpu", 15.0, subsystem="guardian"),
        ]
        groups = a.group_by_subsystem(metrics)
        assert len(groups["kernel"]) == 2
        assert len(groups["guardian"]) == 1


class TestTelemetryReporter:
    def test_generate_report(self):
        r = TelemetryReporter()
        samples = [
            TelemetrySample("s1", [TelemetryMetric("m1", "cpu", 45.0)], 100.0),
            TelemetrySample("s2", [TelemetryMetric("m2", "mem", 60.0)], 200.0),
        ]
        report = r.generate_report("r1", 300.0, samples)
        assert report.total_metrics == 2

    def test_count_samples(self):
        r = TelemetryReporter()
        samples = [TelemetrySample("s1"), TelemetrySample("s2")]
        assert r.count_samples(samples) == 2


# ============================================================
# 3. Conversation Telemetry
# ============================================================

class TestConversationTelemetry:
    def test_queries(self):
        ct = ConversationTelemetry(TelemetryCollector(), MetricsAggregator(),
                                   TelemetryReporter())
        assert ct.get_collector() is not None
        assert ct.get_aggregator() is not None
        assert ct.get_reporter() is not None
        layers = ct.describe_layers()
        assert len(layers) == 3
        assert ct.count_layers() == 3
        assert ct.get_metric_count() == 0
        assert ct.get_sample_count() == 0


# ============================================================
# 4. Dashboard Telemetry
# ============================================================

class TestDashboardTelemetry:
    def test_cards(self):
        dt = DashboardTelemetry(TelemetryCollector(), MetricsAggregator())
        for card in [dt.engine_card(), dt.collector_card(), dt.aggregator_card(),
                     dt.reporter_card(), dt.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        dt = DashboardTelemetry(TelemetryCollector(), MetricsAggregator())
        for card in [dt.engine_card(), dt.collector_card(), dt.aggregator_card(),
                     dt.reporter_card(), dt.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        TelemetryMetric("m", "cpu"),
        TelemetrySample("s"),
        MetricSummary("s", "cpu"),
        TelemetryReport("r", 0.0),
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
def test_metric_parametrized(i):
    c = TelemetryCollector()
    c.record_metric(TelemetryMetric(f"m{i}", f"metric{i % 5}", float(i * 1.5),
                                    "ms" if i % 2 == 0 else "%", f"sub{i % 3}"))
    assert c.count_metrics() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_sample_parametrized(i):
    c = TelemetryCollector()
    metrics = [TelemetryMetric(f"m{j}", f"m{j}", float(j)) for j in range(i % 5)]
    c.create_sample(f"s{i}", float(i * 10), metrics)
    assert c.count_samples() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_summary_parametrized(i):
    a = MetricsAggregator()
    metrics = [TelemetryMetric(f"m{j}", "cpu", float(j * i)) for j in range(i % 6 + 1)]
    s = a.summarize("cpu", metrics)
    assert s.count == i % 6 + 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_report_parametrized(i):
    r = TelemetryReporter()
    samples = [TelemetrySample(f"s{j}", timestamp=float(j)) for j in range(i % 5)]
    report = r.generate_report(f"r{i}", 100.0, samples)
    assert len(report.samples) == i % 5


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    ct = ConversationTelemetry(TelemetryCollector(), MetricsAggregator(),
                               TelemetryReporter())
    assert ct.count_layers() == 3


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    dt = DashboardTelemetry(TelemetryCollector(), MetricsAggregator())
    c = dt.engine_card()
    assert c.status == "ready"
