"""Tests for C-Phase 4 (Workstream C7): Provider Operational Intelligence.

Memverifikasi observer Provider menghasilkan observasi operational provider
(Availability / Readiness / Connectivity / Health / Metrics) secara read-only,
dari metadata ProviderRegistry yang sudah terdaftar (bukan Provider Runtime,
bukan panggilan eksternal, bukan connection/authenticate/retry/execute).
"""
from __future__ import annotations
import dataclasses
import pytest

from sam.providers.registry.provider_registry import ProviderRegistry
from sam.providers.base.provider_descriptor import ProviderDescriptor
from sam.providers.base.provider_capability import ProviderCapability
from sam.providers.base.provider_contract import ProviderContract
from sam.observation.provider_intelligence import (
    ProviderAvailability,
    ProviderAvailabilityReport,
    ProviderConnectivity,
    ProviderConnectivityReport,
    ProviderHealth,
    ProviderHealthReport,
    ProviderIntelligenceObserver,
    ProviderMetrics,
    ProviderReadiness,
    ProviderReadinessReport,
    ProviderTypeMetric,
)


def _registry_with_three() -> ProviderRegistry:
    reg = ProviderRegistry()
    reg.register(ProviderDescriptor(provider_id="openai", name="OpenAI", provider_type="llm"))
    reg.register(ProviderDescriptor(provider_id="sqlite", name="SQLite", provider_type="sqlite"))
    reg.register(ProviderDescriptor(provider_id="docker", name="Docker", provider_type="docker", version="2.0"))
    # attach capability + contract utk satu provider (konektivitas)
    reg.attach_capability(ProviderCapability(provider_id="openai", capability_id="text_gen", name="Text Generation"))
    reg.attach_contract(ProviderContract(provider_id="openai", contract_id="llm_v1", name="LLM v1"))
    return reg


class TestProviderAvailability:
    def test_availability_report(self):
        o = ProviderIntelligenceObserver(_registry_with_three())
        av = o.availability()
        assert isinstance(av, ProviderAvailabilityReport)
        assert av.total_providers == 3
        assert av.registered_count == 3
        assert av.unregistered_count == 0
        assert all(isinstance(e, ProviderAvailability) for e in av.entries)

    def test_availability_as_dict(self):
        o = ProviderIntelligenceObserver(_registry_with_three())
        d = o.availability().as_dict()
        assert "total_providers" in d
        assert "providers" in d


class TestProviderReadiness:
    def test_readiness_report(self):
        o = ProviderIntelligenceObserver(_registry_with_three())
        rd = o.readiness()
        assert isinstance(rd, ProviderReadinessReport)
        assert rd.ready_count + rd.not_ready_count == rd.entries.__len__()
        assert all(isinstance(e, ProviderReadiness) for e in rd.entries)

    def test_state_registered_not_ready(self):
        # status baru daftar = 'registered' (dianggap belum ready)
        o = ProviderIntelligenceObserver(_registry_with_three())
        rd = o.readiness()
        for e in rd.entries:
            assert e.state == "registered"
            assert not e.ready


class TestProviderConnectivity:
    def test_connected_when_capability_or_contract(self):
        o = ProviderIntelligenceObserver(_registry_with_three())
        cn = o.connectivity()
        assert isinstance(cn, ProviderConnectivityReport)
        by_id = {e.provider_id: e for e in cn.entries}
        # openai: ada capability + contract -> connected
        assert by_id["openai"].connected
        # sqlite: tanpa capability/contract -> not connected
        assert not by_id["sqlite"].connected

    def test_connectivity_entry_immutable(self):
        o = ProviderIntelligenceObserver(_registry_with_three())
        cn = o.connectivity()
        assert all(isinstance(e, ProviderConnectivity) for e in cn.entries)


class TestProviderHealth:
    def test_health_derived_from_state(self):
        o = ProviderIntelligenceObserver(_registry_with_three())
        hl = o.health()
        assert isinstance(hl, ProviderHealthReport)
        # semua state 'registered' -> degraded
        assert hl.healthy_count == 0
        assert hl.degraded_count == 3
        assert hl.critical_count == 0
        assert hl.unhealthy_count == hl.degraded_count + hl.critical_count
        assert all(isinstance(e, ProviderHealth) for e in hl.entries)

    def test_health_as_dict(self):
        o = ProviderIntelligenceObserver(_registry_with_three())
        d = o.health().as_dict()
        assert "healthy_count" in d
        assert "unhealthy_count" in d


class TestProviderMetrics:
    def test_metrics_group_by_type(self):
        o = ProviderIntelligenceObserver(_registry_with_three())
        mt = o.metrics()
        assert isinstance(mt, ProviderMetrics)
        assert mt.total_providers == 3
        types = {m.provider_type: m.count for m in mt.by_type}
        assert types.get("llm") == 1
        assert types.get("sqlite") == 1
        assert types.get("docker") == 1

    def test_metrics_entry(self):
        o = ProviderIntelligenceObserver(_registry_with_three())
        mt = o.metrics()
        assert all(isinstance(m, ProviderTypeMetric) for m in mt.by_type)


class TestProviderObserverReadOnly:
    def test_no_registry_mutation(self):
        """Read-only: memanggil observer TIDAK menambah/ubah registry provider."""
        reg0 = ProviderRegistry()
        o = ProviderIntelligenceObserver(reg0)
        o.availability()
        o.readiness()
        o.connectivity()
        o.health()
        o.metrics()
        assert reg0.count() == 0
        assert reg0.list_ids() == []

    def test_does_not_import_runtime_engine(self):
        """C7 tidak boleh import Provider Runtime engine / BaseProvider."""
        import inspect
        from sam.observation import provider_intelligence as m
        src = inspect.getsource(m)
        assert "BaseProvider(" not in src
        assert ".connect(" not in src
        assert ".authenticate(" not in src
        assert ".retry(" not in src

    def test_dto_are_immutable(self):
        for cls in (ProviderAvailability, ProviderAvailabilityReport,
                    ProviderReadiness, ProviderReadinessReport,
                    ProviderConnectivity, ProviderConnectivityReport,
                    ProviderHealth, ProviderHealthReport,
                    ProviderTypeMetric, ProviderMetrics):
            assert dataclasses.is_dataclass(cls)
            assert cls.__dataclass_params__.frozen


class TestProviderWiring:
    def test_wiring_getters_shortcuts(self):
        from sam.runtime_service.api.observation_wiring import (
            get_provider_intelligence_observer,
            observe_providers,
            observe_provider_readiness,
            observe_provider_connectivity,
            observe_provider_health,
            observe_provider_metrics,
        )
        assert isinstance(get_provider_intelligence_observer(), ProviderIntelligenceObserver)
        assert isinstance(observe_providers(), ProviderAvailabilityReport)
        assert isinstance(observe_provider_readiness(), ProviderReadinessReport)
        assert isinstance(observe_provider_connectivity(), ProviderConnectivityReport)
        assert isinstance(observe_provider_health(), ProviderHealthReport)
        assert isinstance(observe_provider_metrics(), ProviderMetrics)
