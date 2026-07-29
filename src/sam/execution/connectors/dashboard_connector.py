# OP-407 — Connector Dashboard
# Python 3.8, frozen DTO, synchronous, presentation only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sam.execution.connector_registry import ConnectorRegistry
from sam.execution.connector_protocol import ConnectorProtocol

from .connector_runtime import ConnectorRuntime, ConnectorRuntimeSnapshot
from .connector_capability import CapabilitySet, CapabilityReport
from .connector_policy import PolicyEvaluator, PolicyDecision
from .connector_health import ConnectorHealthEngine, HealthReport


@dataclass(frozen=True)
class ConnectorSummaryCard:
    total_connectors: int = 0
    filesystem: int = 0
    rest_api: int = 0
    git: int = 0
    shell: int = 0
    other: int = 0
    total_capabilities: int = 0


@dataclass(frozen=True)
class CapabilityCardDTO:
    names: Tuple[str, ...] = field(default_factory=tuple)
    low_risk: int = 0
    medium_risk: int = 0
    high_risk: int = 0
    require_approval: int = 0
    require_guardian: int = 0


@dataclass(frozen=True)
class PolicyCardDTO:
    total: int = 0
    enabled: int = 0
    disabled: int = 0
    names: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class HealthCardDTO:
    overall_healthy: bool = True
    total: int = 0
    healthy: int = 0
    unhealthy: int = 0


@dataclass(frozen=True)
class PreviewCardDTO:
    last_preview: str = ""
    connector_name: str = ""


@dataclass(frozen=True)
class ConnectorDashboard:
    summary: ConnectorSummaryCard = field(default_factory=ConnectorSummaryCard)
    capability: CapabilityCardDTO = field(default_factory=CapabilityCardDTO)
    policy: PolicyCardDTO = field(default_factory=PolicyCardDTO)
    health: HealthCardDTO = field(default_factory=HealthCardDTO)
    preview: PreviewCardDTO = field(default_factory=PreviewCardDTO)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConnectorDashboardBuilder:
    """Builds connector dashboard DTOs — pure composition, no business logic."""

    @staticmethod
    def build(
        registry: ConnectorRegistry,
        runtime: ConnectorRuntime,
        policy_evaluator: PolicyEvaluator,
        health_engine: ConnectorHealthEngine,
    ) -> ConnectorDashboard:
        entries = registry.list()

        # Summary
        fs = sum(1 for e in entries if e.connector_type == "filesystem")
        rest = sum(1 for e in entries if e.connector_type == "rest_api")
        git = sum(1 for e in entries if e.connector_type == "git")
        sh = sum(1 for e in entries if e.connector_type == "shell")
        other = len(entries) - fs - rest - git - sh

        total_caps = sum(len(e.capability_actions) for e in entries)
        summary = ConnectorSummaryCard(
            total_connectors=len(entries),
            filesystem=fs, rest_api=rest, git=git, shell=sh,
            other=other, total_capabilities=total_caps,
        )

        # Capability
        cs = CapabilitySet.all_builtin()
        cap_card = CapabilityCardDTO(
            names=cs.names,
            low_risk=sum(1 for c in cs.capabilities if c.risk_level == "low"),
            medium_risk=sum(1 for c in cs.capabilities if c.risk_level == "medium"),
            high_risk=sum(1 for c in cs.capabilities if c.risk_level == "high"),
            require_approval=len(cs.requires_approval),
            require_guardian=sum(1 for c in cs.capabilities if c.requires_guardian),
        )

        # Policy
        policies = policy_evaluator.list_policies()
        enabled = sum(1 for p in policies if p.enabled)
        disabled = len(policies) - enabled
        policy_card = PolicyCardDTO(
            total=len(policies), enabled=enabled, disabled=disabled,
            names=tuple(p.name for p in policies),
        )

        # Health
        report = health_engine.generate_report()
        health_card = HealthCardDTO(
            overall_healthy=report.overall_healthy,
            total=report.total_connectors,
            healthy=report.healthy_count,
            unhealthy=report.unhealthy_count,
        )

        # Preview
        snapshot = runtime.snapshot()
        preview_card = PreviewCardDTO(
            last_preview="",
            connector_name=f"{snapshot.total_connectors} connectors registered",
        )

        return ConnectorDashboard(
            summary=summary,
            capability=cap_card,
            policy=policy_card,
            health=health_card,
            preview=preview_card,
        )
