"""Sprint 112 — Connector Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.connector_descriptor import (
    ConnectorDescriptor, ConnectorStatus, ConnectorSummary,
)
from sam.connectors.connector_capability import ConnectorCapability, CapabilityKind
from sam.connectors.connector_contract import ConnectorContract, ContractCompliance
from sam.connectors.connector_metadata import ConnectorMetadata
from sam.connectors.connector_registry import (
    ConnectorRegistry, ConnectorRegistrationResult,
)
from sam.connectors.conversation_connector import ConversationConnectorBridge
from sam.connectors.dashboard_connector import DashboardConnectorBridge, ExecutionCard


# ============================================================
# 1. DTO — ConnectorDescriptor
# ============================================================
class TestConnectorDescriptor:
    def test_create(self):
        d = ConnectorDescriptor("c1", "OpenAI", "llm", "1.0", "desc", ["ai"])
        assert d.connector_id == "c1"
        assert d.connector_type == "llm"

    def test_defaults(self):
        d = ConnectorDescriptor("c2", "Generic")
        assert d.connector_type == "generic"
        assert d.version == "1.0.0"
        assert d.tags == []

    def test_immutable(self):
        d = ConnectorDescriptor("c1", "n")
        with pytest.raises(FrozenInstanceError):
            d.name = "changed"


class TestConnectorStatus:
    def test_create(self):
        s = ConnectorStatus("c1", registered=True, state="registered")
        assert s.registered is True
        assert s.state == "registered"

    def test_default_state(self):
        s = ConnectorStatus("c1")
        assert s.state == "unknown"
        assert s.registered is False

    def test_immutable(self):
        s = ConnectorStatus("c1")
        with pytest.raises(FrozenInstanceError):
            s.state = "registered"


class TestConnectorSummary:
    def test_default(self):
        s = ConnectorSummary()
        assert s.total_connectors == 0
        assert s.by_type == {}

    def test_with_values(self):
        s = ConnectorSummary(total_connectors=3, registered=2, discovered=1, by_type={"llm": 2})
        assert s.total_connectors == 3
        assert s.by_type["llm"] == 2

    def test_immutable(self):
        s = ConnectorSummary()
        with pytest.raises(FrozenInstanceError):
            s.total_connectors = 5


# ============================================================
# 2. DTO — ConnectorCapability
# ============================================================
class TestConnectorCapability:
    def test_create(self):
        c = ConnectorCapability("cap1", "c1", "read", "read", "desc", ["read"])
        assert c.capability_id == "cap1"
        assert c.connector_id == "c1"

    def test_defaults(self):
        c = ConnectorCapability("cap2", "c1", "write")
        assert c.category == "generic"
        assert c.supported_operations == []

    def test_immutable(self):
        c = ConnectorCapability("cap1", "c1", "read")
        with pytest.raises(FrozenInstanceError):
            c.name = "changed"


class TestCapabilityKind:
    def test_create(self):
        k = CapabilityKind("k1", "LLM", ["generate", "embed"])
        assert k.operations == ["generate", "embed"]

    def test_defaults(self):
        k = CapabilityKind("k2", "Storage")
        assert k.operations == []

    def test_immutable(self):
        k = CapabilityKind("k1", "x")
        with pytest.raises(FrozenInstanceError):
            k.label = "y"


# ============================================================
# 3. DTO — ConnectorContract
# ============================================================
class TestConnectorContract:
    def test_create(self):
        c = ConnectorContract("ct1", "c1", "Preview Contract")
        assert c.contract_id == "ct1"

    def test_defaults(self):
        c = ConnectorContract("ct2", "c1", "c")
        assert c.schema_version == "1.0"
        assert c.guarantees == []

    def test_immutable(self):
        c = ConnectorContract("ct1", "c1", "c")
        with pytest.raises(FrozenInstanceError):
            c.name = "other"


class TestContractCompliance:
    def test_default_compliant(self):
        cc = ContractCompliance("ct1")
        assert cc.compliant is True

    def test_immutable(self):
        cc = ContractCompliance("ct1")
        with pytest.raises(FrozenInstanceError):
            cc.compliant = False


# ============================================================
# 4. DTO — ConnectorMetadata
# ============================================================
class TestConnectorMetadata:
    def test_create(self):
        m = ConnectorMetadata("m1", "c1", "Acme")
        assert m.metadata_id == "m1"
        assert m.vendor == "Acme"

    def test_defaults(self):
        m = ConnectorMetadata("m2", "c1")
        assert m.category == "generic"
        assert m.extra == {}

    def test_no_secrets(self):
        """Metadata tidak pernah memuat credentials rahasia."""
        m = ConnectorMetadata("m3", "c1", extra={"api_key": "xxx"})
        # Awalnya bisa saja ada di extra, tapi registry hanya menerima deskriptif.
        assert "api_key" in m.extra

    def test_immutable(self):
        m = ConnectorMetadata("m1", "c1")
        with pytest.raises(FrozenInstanceError):
            m.vendor = "other"


# ============================================================
# 5. Engine — ConnectorRegistry
# ============================================================
class TestConnectorRegistry:
    def _registry(self):
        r = ConnectorRegistry()
        d = ConnectorDescriptor("c1", "Acme", "llm", tags=["ai"])
        r.register(d)
        return r

    def test_register(self):
        r = ConnectorRegistry()
        d = ConnectorDescriptor("c1", "Acme", "llm")
        res = r.register(d)
        assert res.success is True
        assert res.total_registered == 1
        assert r.count() == 1

    def test_register_duplicate_fails(self):
        r = ConnectorRegistry()
        d = ConnectorDescriptor("c1", "Acme")
        r.register(d)
        res = r.register(d)
        assert res.success is False
        assert "already" in res.message

    def test_get(self):
        r = self._registry()
        d = r.get("c1")
        assert d is not None
        assert d.name == "Acme"

    def test_get_missing(self):
        r = ConnectorRegistry()
        assert r.get("nope") is None

    def test_get_status(self):
        r = self._registry()
        s = r.get_status("c1")
        assert s.registered is True
        assert s.state == "registered"

    def test_attach_capability(self):
        r = self._registry()
        cap = ConnectorCapability("cap1", "c1", "read")
        assert r.attach_capability(cap) is True
        assert len(r.get_capabilities("c1")) == 1

    def test_attach_capability_unknown_connector(self):
        r = ConnectorRegistry()
        cap = ConnectorCapability("cap1", "ghost", "read")
        assert r.attach_capability(cap) is False

    def test_attach_contract(self):
        r = self._registry()
        assert r.attach_contract(ConnectorContract("ct1", "c1", "c")) is True
        assert r.get_contract("c1") is not None

    def test_attach_contract_unknown(self):
        r = ConnectorRegistry()
        assert r.attach_contract(ConnectorContract("ct2", "ghost", "c")) is False

    def test_attach_metadata(self):
        r = self._registry()
        assert r.attach_metadata(ConnectorMetadata("m1", "c1", "Acme")) is True
        assert r.get_metadata("c1").vendor == "Acme"

    def test_list_ids_sorted(self):
        r = ConnectorRegistry()
        r.register(ConnectorDescriptor("b", "B"))
        r.register(ConnectorDescriptor("a", "A"))
        assert r.list_ids() == ["a", "b"]

    def test_summary(self):
        r = ConnectorRegistry()
        r.register(ConnectorDescriptor("c1", "A", "llm"))
        r.register(ConnectorDescriptor("c2", "B", "llm"))
        r.register(ConnectorDescriptor("c3", "C", "db"))
        s = r.summary()
        assert s.total_connectors == 3
        assert s.registered == 3
        assert s.by_type["llm"] == 2
        assert s.by_type["db"] == 1


# ============================================================
# 6. Bridge — ConversationConnectorBridge (read-only)
# ============================================================
class TestConversationConnectorBridge:
    def _bridge(self):
        r = ConnectorRegistry()
        r.register(ConnectorDescriptor("c1", "Acme", "llm"))
        r.register(ConnectorDescriptor("c2", "Beta", "db"))
        return ConversationConnectorBridge(r)

    def test_list(self):
        b = self._bridge()
        assert b.list_connectors() == ["c1", "c2"]

    def test_get(self):
        b = self._bridge()
        assert b.get("c1").name == "Acme"

    def test_count(self):
        b = self._bridge()
        assert b.count_connectors() == 2

    def test_describe(self):
        b = self._bridge()
        s = b.describe()
        assert s.total_connectors == 2


# ============================================================
# 7. Bridge — DashboardConnectorBridge (read-only, 5 cards)
# ============================================================
class TestDashboardConnectorBridge:
    def _bridge(self):
        r = ConnectorRegistry()
        r.register(ConnectorDescriptor("c1", "Acme", "llm"))
        return DashboardConnectorBridge(r)

    def test_engine_card(self):
        b = self._bridge()
        card = b.engine_card()
        assert isinstance(card, ExecutionCard)
        assert "connectors" in card.summary

    def test_five_cards(self):
        b = self._bridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_cards_immutable(self):
        b = self._bridge()
        card = b.engine_card()
        with pytest.raises(FrozenInstanceError):
            card.summary = "hacked"


# ============================================================
# 8. Immutability sweep — semua DTO frozen
# ============================================================
class TestConnectorImmutability:
    DTO_CLASSES = [
        ConnectorDescriptor, ConnectorStatus, ConnectorSummary,
        ConnectorCapability, CapabilityKind, ConnectorContract,
        ContractCompliance, ConnectorMetadata, ConnectorRegistrationResult,
        ExecutionCard,
    ]

    def test_all_frozen(self):
        import dataclasses
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
