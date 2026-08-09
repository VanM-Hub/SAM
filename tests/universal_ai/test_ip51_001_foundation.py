"""Test IP-5.1-001 - Universal AI Provider Foundation (MISSION-5.1).

Coverage: WP-01..WP-10 - identity, registry, descriptor, model, capability,
discovery, health, API, compliance, integration.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.universal_ai import (
    AICapability,
    AICapabilityKind,
    AICapabilityModel,
    AIProviderAPI,
    AIProviderComplianceChecker,
    AIProviderDiscovery,
    AIProviderHealthCheck,
    AIProviderRegistry,
    AIModelDescriptor,
    HealthState,
    ModelCapability,
    ProviderDescriptor,
    ProviderIdentity,
    ProviderType,
)


# ---------------------------------------------------------------------------
# WP-01 AI Provider Identity
# ---------------------------------------------------------------------------

def _identity(pid="prov-1", name="OpenAI", ptype=ProviderType.CLOUD):
    return ProviderIdentity(provider_id=pid, name=name, provider_type=ptype)


class TestProviderIdentity:
    def test_well_formed(self):
        assert _identity().is_well_formed is True

    def test_immutable(self):
        ident = _identity()
        try:
            ident.provider_id = "changed"  # type: ignore[misc]
            assert False, "should be frozen/immutable"
        except Exception:
            pass

    def test_not_authority_marker(self):
        ident = _identity()
        assert "authority" not in ident.as_dict()


# ---------------------------------------------------------------------------
# WP-02 AI Provider Registry
# ---------------------------------------------------------------------------

class TestProviderRegistry:
    def test_register_and_lookup(self):
        registry = AIProviderRegistry()
        registry.register(_identity())
        assert registry.lookup("prov-1") is not None

    def test_lookup_missing_returns_none(self):
        assert AIProviderRegistry().lookup("nope") is None

    def test_list_and_validate(self):
        registry = AIProviderRegistry()
        registry.register(_identity())
        registry.register(_identity("prov-2", "Anthropic"))
        assert registry.size() == 2
        assert registry.validate_registry() is True

    def test_availability(self):
        registry = AIProviderRegistry()
        registry.register(_identity(), availability=True)
        registry.register(_identity("prov-2", "B"), availability=False)
        assert len(registry.available()) == 1

    def test_remove(self):
        registry = AIProviderRegistry()
        registry.register(_identity())
        assert registry.remove("prov-1") is True
        assert registry.remove("prov-1") is False


# ---------------------------------------------------------------------------
# WP-03 / WP-04 Descriptor & Model
# ---------------------------------------------------------------------------

class TestDescriptors:
    def test_provider_descriptor(self):
        prov = _identity()
        model = AIModelDescriptor(
            model_id="m1", name="gpt", provider_id="prov-1",
            capability=ModelCapability(supports_text_generation=True, context_window=8000),
        )
        desc = ProviderDescriptor(identity=prov, supported_models=(model,))
        assert desc.model("m1") is model
        assert desc.model("x") is None
        assert desc.as_dict()["identity"]["provider_id"] == "prov-1"

    def test_model_provider_distinct(self):
        # Model harus dapat dibedakan dari provider
        model = AIModelDescriptor(model_id="m1", name="gpt", provider_id="prov-1")
        prov = _identity()
        assert model.provider_id == prov.provider_id
        assert model.model_id != prov.provider_id


# ---------------------------------------------------------------------------
# WP-05 AI Capability Model
# ---------------------------------------------------------------------------

class TestCapabilityModel:
    def test_has_and_kinds(self):
        model = AICapabilityModel(
            (AICapability(AICapabilityKind.TEXT_GENERATION, "text"),)
        )
        assert model.has(AICapabilityKind.TEXT_GENERATION) is True
        assert model.has(AICapabilityKind.VISION) is False
        assert model.kinds() == (AICapabilityKind.TEXT_GENERATION,)


# ---------------------------------------------------------------------------
# WP-06 AI Provider Discovery
# ---------------------------------------------------------------------------

class TestDiscovery:
    def _setup(self):
        registry = AIProviderRegistry()
        registry.register(_identity(), availability=True)
        model = AIModelDescriptor(
            model_id="m1", name="gpt", provider_id="prov-1",
            capability=ModelCapability(supports_text_generation=True, context_window=8000),
        )
        desc = ProviderDescriptor(identity=_identity(), supported_models=(model,))
        return registry, AIProviderDiscovery(registry, (desc,))

    def test_discover_providers(self):
        registry, discovery = self._setup()
        assert len(discovery.discover_providers()) == 1

    def test_discover_models(self):
        registry, discovery = self._setup()
        assert len(discovery.discover_models("prov-1")) == 1

    def test_discover_capability(self):
        registry, discovery = self._setup()
        found = discovery.discover_capability(AICapabilityKind.TEXT_GENERATION)
        assert len(found) >= 1

    def test_no_support_returns_empty(self):
        registry, discovery = self._setup()
        assert discovery.discover_capability(AICapabilityKind.VISION) == ()


# ---------------------------------------------------------------------------
# WP-07 AI Provider Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_healthy_when_ready(self):
        health = AIProviderHealthCheck().assess("prov-1")
        assert health.state == HealthState.READY
        assert health.healthy is True

    def test_failed_on_error(self):
        health = AIProviderHealthCheck().assess("prov-1", error="boom")
        assert health.failure_state is True

    def test_degraded_on_latency(self):
        health = AIProviderHealthCheck().assess("prov-1", latency_ms=9000)
        assert health.state == HealthState.DEGRADED


# ---------------------------------------------------------------------------
# WP-08 AI Provider API
# ---------------------------------------------------------------------------

class TestProviderAPI:
    def test_full_api_flow(self):
        api = AIProviderAPI()
        api.register(_identity(), availability=True)
        assert api.lookup("prov-1") is not None
        assert len(api.list_providers()) == 1
        assert len(api.discover()) == 1
        model = AIModelDescriptor(model_id="m1", name="gpt", provider_id="prov-1")
        api.set_descriptors((ProviderDescriptor(identity=_identity(), supported_models=(model,)),))
        assert len(api.discover_models("prov-1")) == 1
        assert api.health("prov-1").healthy is True
        assert api.health("missing") is None


# ---------------------------------------------------------------------------
# WP-09 AI Provider Compliance
# ---------------------------------------------------------------------------

class TestProviderCompliance:
    def test_certify_passes(self):
        registry = AIProviderRegistry()
        registry.register(_identity())
        checker = AIProviderComplianceChecker()
        cert = checker.certify(registry)
        assert cert["certified"] is True

    def test_fails_on_boundary_violation(self):
        registry = AIProviderRegistry()
        registry.register(_identity())
        cert = AIProviderComplianceChecker().certify(registry, no_execution_bypass=False)
        assert cert["certified"] is False


# ---------------------------------------------------------------------------
# WP-10 Integration & Certification
# ---------------------------------------------------------------------------

class TestFoundationIntegration:
    def test_end_to_end(self):
        api = AIProviderAPI()
        api.register(_identity(), availability=True)
        model = AIModelDescriptor(
            model_id="m1", name="gpt", provider_id="prov-1",
            capability=ModelCapability(supports_text_generation=True, context_window=8000),
        )
        api.set_descriptors((ProviderDescriptor(identity=_identity(), supported_models=(model,)),))
        assert len(api.discover()) == 1
        assert len(api.discover_models("prov-1")) == 1
        cert = AIProviderComplianceChecker().certify(api.registry)
        assert cert["certified"] is True
