"""Sprint 144 — Provider Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.providers.base.provider_descriptor import (
    ProviderDescriptor, ProviderStatus, ProviderSummary,
)
from sam.providers.base.provider_capability import ProviderCapability, ProviderOperation
from sam.providers.base.provider_contract import ProviderContract, ProviderContractCompliance
from sam.providers.base.protocol import ProviderProtocol, ProtocolCompliance
from sam.providers.base.base_provider import BaseProvider, ProviderError
from sam.providers.registry.provider_registry import ProviderRegistry
from sam.providers.registry.provider_builder import ProviderBuilder
from sam.providers.conversation.conversation_provider import ConversationProviderBridge
from sam.providers.dashboard.dashboard_provider import DashboardProviderBridge, ExecutionCard
from sam.providers.runtime.provider_runtime import (
    ProviderRuntime, ProviderRuntimeCheck, ProviderRuntimeReadiness,
)


def _ready_registry():
    r = ProviderRegistry()
    r.register(ProviderDescriptor("p1", "Filesystem", "filesystem"))
    r.attach_capability(ProviderCapability(
        "cap1", "p1", "read", "filesystem",
        operations=[ProviderOperation("read"), ProviderOperation("write")],
    ))
    r.attach_contract(ProviderContract("ct1", "p1", "fs-contract"))
    return r


# ============================================================
# DTO — Descriptor / Status / Summary
# ============================================================
class TestProviderDescriptor:
    def test_default(self):
        d = ProviderDescriptor("p1", "Filesystem")
        assert d.provider_type == "generic"
        assert d.implements == []

    def test_immutable(self):
        d = ProviderDescriptor("p1", "Filesystem")
        with pytest.raises(FrozenInstanceError):
            d.provider_type = "filesystem"


class TestProviderStatus:
    def test_default(self):
        s = ProviderStatus("p1")
        assert s.state == "unknown"

    def test_immutable(self):
        s = ProviderStatus("p1")
        with pytest.raises(FrozenInstanceError):
            s.registered = True


class TestProviderSummary:
    def test_default(self):
        s = ProviderSummary()
        assert s.total_providers == 0

    def test_immutable(self):
        s = ProviderSummary()
        with pytest.raises(FrozenInstanceError):
            s.total_providers = 5


# ============================================================
# DTO — Capability / Operation
# ============================================================
class TestProviderOperation:
    def test_preview_default(self):
        op = ProviderOperation("read")
        assert op.preview_only is True


class TestProviderCapability:
    def test_supports(self):
        c = ProviderCapability(
            "cap1", "p1", "read", "filesystem",
            operations=[ProviderOperation("read"), ProviderOperation("write")],
        )
        assert c.supports("read")
        assert c.supports("write")
        assert not c.supports("delete")

    def test_immutable(self):
        c = ProviderCapability("cap1", "p1", "read")
        with pytest.raises(FrozenInstanceError):
            c.name = "write"


# ============================================================
# DTO — Contract / Compliance / Protocol
# ============================================================
class TestProviderContract:
    def test_default(self):
        c = ProviderContract("ct1", "p1", "fs")
        assert c.schema_version == "1.0"

    def test_immutable(self):
        c = ProviderContract("ct1", "p1", "fs")
        with pytest.raises(FrozenInstanceError):
            c.name = "other"


class TestProviderContractCompliance:
    def test_default_compliant(self):
        c = ProviderContractCompliance("ct1", "p1")
        assert c.compliant is True


class TestProviderProtocol:
    def test_readonly_default(self):
        p = ProviderProtocol("pr1", "p1")
        assert p.readonly is True


class TestProtocolCompliance:
    def test_default(self):
        p = ProtocolCompliance("pr1")
        assert p.compliant is True


# ============================================================
# Engine — BaseProvider
# ============================================================
class TestBaseProvider:
    def _provider(self):
        class MyProvider(BaseProvider):
            descriptor = ProviderDescriptor("mp", "Mock", "filesystem")
            capabilities = [ProviderCapability(
                "cap1", "mp", "read", "filesystem",
                operations=[ProviderOperation("read")],
            )]
            contract = ProviderContract("ct1", "mp", "mock")

        return MyProvider()

    def test_describe(self):
        assert self._provider().describe().provider_id == "mp"

    def test_supports(self):
        assert self._provider().supports("read")
        assert not self._provider().supports("delete")

    def test_preview_no_exec(self):
        p = self._provider()
        result = p.preview("read", {"path": "/tmp/a.txt"})
        assert result["preview"] is True
        assert result["external_calls"] == 0

    def test_preview_unsupported_raises(self):
        with pytest.raises(ProviderError):
            self._provider().preview("delete", {})

    def test_external_calls_always_zero(self):
        p = self._provider()
        p.preview("read", {})
        p.preview("read", {})
        assert p.preview_count == 2
        assert p.external_calls == 0


# ============================================================
# Engine — ProviderRegistry / Builder
# ============================================================
class TestProviderRegistry:
    def test_register(self):
        r = ProviderRegistry()
        r.register(ProviderDescriptor("p1", "Filesystem", "filesystem"))
        assert r.count() == 1
        assert r.list_ids() == ["p1"]

    def test_duplicate_rejected(self):
        r = ProviderRegistry()
        assert r.register(ProviderDescriptor("p1", "x"))
        assert not r.register(ProviderDescriptor("p1", "y"))

    def test_summary(self):
        r = _ready_registry()
        s = r.summary()
        assert s.total_providers == 1
        assert s.by_type == {"filesystem": 1}


class TestProviderBuilder:
    def test_build_single(self):
        class P(BaseProvider):
            descriptor = ProviderDescriptor("p1", "FS", "filesystem")
            capabilities = [ProviderCapability(
                "cap1", "p1", "read", "filesystem",
                operations=[ProviderOperation("read")],
            )]
            contract = ProviderContract("ct1", "p1", "fs")

        builder = ProviderBuilder()
        assert builder.add(P()) is True
        registry = builder.build()
        assert registry.count() == 1
        assert len(registry.get_capabilities("p1")) == 1
        assert registry.get_contract("p1") is not None


# ============================================================
# Bridges
# ============================================================
class TestConversationProviderBridge:
    def test_describe(self):
        b = ConversationProviderBridge(_ready_registry())
        assert b.describe().total_providers == 1

    def test_list(self):
        b = ConversationProviderBridge(_ready_registry())
        assert b.list_providers() == ["p1"]

    def test_capabilities(self):
        b = ConversationProviderBridge(_ready_registry())
        assert b.capabilities("p1") == ["read"]

    def test_count(self):
        b = ConversationProviderBridge(_ready_registry())
        assert b.count() == 1


class TestDashboardProviderBridge:
    def test_cards(self):
        b = DashboardProviderBridge(_ready_registry())
        cards = b.cards()
        assert len(cards) == 1
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_card_verdict(self):
        b = DashboardProviderBridge(_ready_registry())
        assert b.card("p1").verdict == "ready"

    def test_card_missing(self):
        b = DashboardProviderBridge(_ready_registry())
        assert b.card("nope").verdict == "missing"


# ============================================================
# Runtime
# ============================================================
class TestProviderRuntime:
    def test_readiness_ready(self):
        rt = ProviderRuntime(_ready_registry())
        assert rt.readiness().ready is True

    def test_readiness_empty(self):
        rt = ProviderRuntime(ProviderRegistry())
        assert rt.readiness().ready is False

    def test_status(self):
        rt = ProviderRuntime(_ready_registry())
        assert rt.status() is True

    def test_runtime_version(self):
        assert ProviderRuntime.RUNTIME_VERSION == "1.0.0"


# ============================================================
# Immutability
# ============================================================
class TestProviderFoundationImmutability:
    DTO_CLASSES = [
        ProviderDescriptor, ProviderStatus, ProviderSummary,
        ProviderCapability, ProviderOperation, ProviderContract,
        ProviderContractCompliance, ProviderProtocol, ProtocolCompliance,
        ProviderRuntimeCheck, ProviderRuntimeReadiness, ExecutionCard,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
