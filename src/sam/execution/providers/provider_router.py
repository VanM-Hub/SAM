# OP-444 — Provider Router
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .provider_protocol import ExecutionProviderProtocol, ProviderRequest, ProviderResponse
from .provider_registry import ProviderRegistry

from sam.execution.adapters.execution_envelope import ExecutionEnvelope


@dataclass(frozen=True)
class RoutingRule:
    rule_id: str = ""
    source_type: str = ""
    target_provider_type: str = ""
    action_match: str = "*"
    priority: int = 0


@dataclass(frozen=True)
class RouteDecision:
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    envelope_id: str = ""
    selected_provider_type: str = ""
    selected_provider_id: str = ""
    provider_name: str = ""
    actions_matched: Tuple[str, ...] = field(default_factory=tuple)
    validation_passed: bool = True
    preview_response: Optional[ProviderResponse] = None
    routing_notes: str = ""


@dataclass(frozen=True)
class ProviderSelection:
    provider: Optional[ExecutionProviderProtocol] = None
    matched: bool = False
    confidence: float = 1.0
    notes: str = ""


@dataclass(frozen=True)
class RoutingSummary:
    total_decisions: int = 0
    successful: int = 0
    failed: int = 0
    provider_types: Tuple[str, ...] = field(default_factory=tuple)
    average_confidence: float = 0.0


class ProviderRouter:
    """Routes execution envelopes to appropriate providers."""

    def __init__(self, registry: ProviderRegistry):
        self._registry = registry
        self._rules: List[RoutingRule] = []

    def add_rule(self, rule: RoutingRule) -> None:
        self._rules.append(rule)

    def clear_rules(self) -> None:
        self._rules.clear()

    def get_rules(self) -> Tuple[RoutingRule, ...]:
        return tuple(self._rules)

    def route(self, envelope: ExecutionEnvelope,
              preferred_type: Optional[str] = None) -> RouteDecision:
        action = envelope.items[0].action if envelope.items else ""

        # Try preferred type first
        if preferred_type:
            providers = self._registry.find_by_type(preferred_type)
            if providers:
                p = providers[0]
                pr = ProviderRequest(envelope=envelope, provider_type=preferred_type, action=action)
                resp = p.execute_preview(pr)
                return RouteDecision(envelope_id=envelope.envelope_id,
                    selected_provider_type=preferred_type,
                    selected_provider_id=p.metadata.provider_id,
                    provider_name=p.metadata.name,
                    actions_matched=(action,),
                    validation_passed=True,
                    preview_response=resp)

        # Match by action
        providers = self._registry.find_by_action(action)
        if providers:
            p = providers[0]
            pr = ProviderRequest(envelope=envelope, provider_type=p.metadata.provider_type, action=action)
            resp = p.execute_preview(pr)
            return RouteDecision(envelope_id=envelope.envelope_id,
                selected_provider_type=p.metadata.provider_type,
                selected_provider_id=p.metadata.provider_id,
                provider_name=p.metadata.name,
                actions_matched=(action,),
                validation_passed=True,
                preview_response=resp)

        # No match
        return RouteDecision(envelope_id=envelope.envelope_id,
            validation_passed=False,
            routing_notes=f"No provider found for action '{action}'")

    def select(self, provider_type: str) -> ProviderSelection:
        providers = self._registry.find_by_type(provider_type)
        if providers:
            return ProviderSelection(provider=providers[0], matched=True)
        return ProviderSelection(matched=False, notes=f"No provider for type '{provider_type}'")

    def get_summary(self, decisions: Tuple[RouteDecision, ...]) -> RoutingSummary:
        succ = sum(1 for d in decisions if d.validation_passed)
        fail = len(decisions)-succ
        types = tuple(set(d.selected_provider_type for d in decisions if d.selected_provider_type))
        return RoutingSummary(total_decisions=len(decisions), successful=succ, failed=fail,
            provider_types=types, average_confidence=1.0 if succ==len(decisions) else 0.5)
