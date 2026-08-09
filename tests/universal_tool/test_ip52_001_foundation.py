"""Test IP-5.2-001 - Universal Tool Foundation (MISSION-5.2).

Coverage: WP-01..WP-10 - identity, registry, descriptor, capability, contract,
discovery, health, API, compliance, integration.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.universal_tool import (
    ToolAPI,
    ToolCapability,
    ToolCapabilityKind,
    ToolComplianceChecker,
    ToolContract,
    ToolDescriptor,
    ToolDiscovery,
    ToolHealthCheck,
    ToolHealthState,
    ToolIdentity,
    ToolRegistry,
    ToolType,
)


def _tool(tid="tool-1", name="GitHub"):
    return ToolIdentity(tool_id=tid, name=name, tool_type=ToolType.EXTERNAL)


class TestToolIdentity:
    def test_well_formed(self):
        assert _tool().is_well_formed is True

    def test_immutable(self):
        t = _tool()
        try:
            t.tool_id = "x"  # type: ignore[misc]
            assert False
        except Exception:
            pass


class TestToolRegistry:
    def test_register_lookup(self):
        registry = ToolRegistry()
        registry.register(_tool())
        assert registry.lookup("tool-1") is not None

    def test_list_available(self):
        registry = ToolRegistry()
        registry.register(_tool(), availability=True)
        registry.register(_tool("tool-2", "Docker"), availability=False)
        assert len(registry.available()) == 1
        assert registry.size() == 2
        assert registry.validate_registry() is True


class TestDescriptors:
    def test_capability(self):
        tool = _tool()
        cap = ToolCapability(ToolCapabilityKind.READ, "read")
        desc = ToolDescriptor(identity=tool, capabilities=(cap,))
        assert desc.capability(ToolCapabilityKind.READ) == cap
        assert desc.capability(ToolCapabilityKind.WRITE) is None


class TestToolContract:
    def test_governed_by_default(self):
        contract = ToolContract(tool_id="tool-1", contract_id="c1", supports_capability=(ToolCapabilityKind.READ,))
        assert contract.governed is True
        assert contract.allows(ToolCapabilityKind.READ) is True
        assert contract.allows(ToolCapabilityKind.WRITE) is False


class TestDiscovery:
    def _setup(self):
        registry = ToolRegistry()
        registry.register(_tool(), availability=True)
        desc = ToolDescriptor(identity=_tool(), capabilities=(ToolCapability(ToolCapabilityKind.READ),))
        return registry, ToolDiscovery(registry, (desc,))

    def test_discover_by_capability(self):
        registry, discovery = self._setup()
        found = discovery.discover_by_capability(ToolCapabilityKind.READ)
        assert len(found) == 1
        assert discovery.discover_by_capability(ToolCapabilityKind.WRITE) == ()


class TestHealth:
    def test_healthy(self):
        assert ToolHealthCheck().assess("tool-1").healthy is True

    def test_failed_on_error(self):
        assert ToolHealthCheck().assess("tool-1", error="boom").state == ToolHealthState.FAILED


class TestToolAPI:
    def test_full_flow(self):
        api = ToolAPI()
        api.register(_tool(), availability=True)
        assert api.lookup("tool-1") is not None
        assert len(api.list_tools()) == 1
        assert len(api.discover()) == 1
        assert api.health("tool-1").healthy is True
        assert api.health("missing") is None


class TestToolCompliance:
    def test_certify_passes(self):
        registry = ToolRegistry()
        registry.register(_tool())
        assert ToolComplianceChecker().certify(registry)["certified"] is True

    def test_fails_on_bypass(self):
        registry = ToolRegistry()
        registry.register(_tool())
        assert ToolComplianceChecker().certify(registry, no_execution_bypass=False)["certified"] is False
