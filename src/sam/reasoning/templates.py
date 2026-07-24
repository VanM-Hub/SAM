"""
Graph Templates – Sprint 22 Fase 2

Pre-defined execution graph templates keyed by intent type.
The Planning Engine uses these templates as starting points
that get customised and enriched with knowledge before execution.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict

from .intent import IntentType


# ── Graph Template Model ──────────────────────────────────────────────


class GraphTemplate(BaseModel):
    """A reusable blueprint for generating Execution Graphs from Intents.

    Templates define the structural skeleton — node definitions,
    dependencies, and default policies — that the Planning Engine
    fills in with concrete capability IDs, parameters, and context.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique template identifier",
    )
    intent_type: IntentType = Field(
        description="Which intent type this template serves",
    )
    name: str = Field(description="Human-readable template name")
    description: str = Field(description="What this template does")
    nodes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Template node definitions (with placeholders for capability IDs)",
    )
    dependencies: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Template dependency edges: {from: node_id, to: node_id}",
    )
    retry_policy: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Default retry policy applied to all nodes (overridable per-node)",
    )
    compensation_policy: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Default compensation policy applied to all nodes (overridable per-node)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional template metadata (tags, version, author, etc.)",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="When the template was created",
    )

    def get_node_ids(self) -> Set[str]:
        """Return the set of all node IDs defined in this template."""
        return {n["id"] for n in self.nodes if "id" in n}

    def get_entry_node_ids(self) -> List[str]:
        """Return node IDs that have no incoming dependency edges."""
        all_ids = self.get_node_ids()
        has_incoming: Set[str] = set()
        for dep in self.dependencies:
            to_id = dep.get("to", "")
            if to_id in all_ids:
                has_incoming.add(to_id)
        return sorted(all_ids - has_incoming)

    def get_exit_node_ids(self) -> List[str]:
        """Return node IDs that have no outgoing dependency edges."""
        all_ids = self.get_node_ids()
        has_outgoing: Set[str] = set()
        for dep in self.dependencies:
            from_id = dep.get("from", "")
            if from_id in all_ids:
                has_outgoing.add(from_id)
        return sorted(all_ids - has_outgoing)


# ── Built-In Templates ────────────────────────────────────────────────


def _tmpl_diagnose_runtime() -> GraphTemplate:
    """Template for diagnosing a provider/runtime health issue."""
    return GraphTemplate(
        id="tmpl-diagnose-runtime",
        intent_type=IntentType.DIAGNOSE,
        name="Diagnose Runtime",
        description="Run health checks on a target provider, test connectivity, and generate a diagnostic report.",
        nodes=[
            {
                "id": "health-check",
                "capability_id": "{target}:health-check",
                "inputs": {"target": "{target}", "verbose": "{verbose}"},
                "retry_policy": {"max_attempts": 1},
            },
            {
                "id": "provider-test",
                "capability_id": "{target}:connectivity-test",
                "inputs": {"target": "{target}"},
                "retry_policy": {"max_attempts": 2, "initial_delay": 2},
            },
            {
                "id": "report",
                "capability_id": "core:generate-report",
                "inputs": {"title": "Diagnostic Report: {target}", "include_logs": True},
            },
        ],
        dependencies=[
            {"from": "health-check", "to": "provider-test"},
            {"from": "provider-test", "to": "report"},
        ],
        metadata={"version": "1.0", "author": "sam-builtin"},
    )


def _tmpl_repair_provider() -> GraphTemplate:
    """Template for repairing a provider that is in a degraded/failed state."""
    return GraphTemplate(
        id="tmpl-repair-provider",
        intent_type=IntentType.REPAIR,
        name="Repair Provider",
        description="Diagnose the issue, generate a repair plan, get approval, execute fix, and verify recovery.",
        nodes=[
            {
                "id": "diagnose",
                "capability_id": "{target}:health-check",
                "inputs": {"target": "{target}", "deep_scan": True},
            },
            {
                "id": "plan",
                "capability_id": "core:generate-repair-plan",
                "inputs": {"target": "{target}", "diagnosis": "{diagnose.output}"},
            },
            {
                "id": "approve",
                "capability_id": "governance:request-approval",
                "inputs": {"plan": "{plan.output}", "target": "{target}"},
                "retry_policy": {"max_attempts": 1},
            },
            {
                "id": "execute",
                "capability_id": "{target}:repair",
                "inputs": {"plan": "{plan.output}", "approval": "{approve.output}"},
                "retry_policy": {"max_attempts": 3, "initial_delay": 5},
                "compensation_policy": {
                    "compensation_node_id": "rollback",
                    "on_failure": "COMPENSATE",
                },
            },
            {
                "id": "rollback",
                "capability_id": "{target}:rollback",
                "inputs": {"target": "{target}"},
            },
            {
                "id": "verify",
                "capability_id": "{target}:health-check",
                "inputs": {"target": "{target}", "compare_to": "{diagnose.output}"},
            },
        ],
        dependencies=[
            {"from": "diagnose", "to": "plan"},
            {"from": "plan", "to": "approve"},
            {"from": "approve", "to": "execute"},
            {"from": "execute", "to": "verify"},
        ],
        retry_policy={"max_attempts": 2, "backoff": "EXPONENTIAL", "initial_delay": 1, "max_delay": 30, "jitter": True},
        metadata={"version": "1.0", "author": "sam-builtin", "risk_score": 0.6, "requires_approval": True},
    )


def _tmpl_deploy_workspace() -> GraphTemplate:
    """Template for deploying a capability/plugin to a workspace."""
    return GraphTemplate(
        id="tmpl-deploy-workspace",
        intent_type=IntentType.DEPLOY,
        name="Deploy to Workspace",
        description="Validate pre-deploy conditions, deploy the capability, verify it, and compensate if anything fails.",
        nodes=[
            {
                "id": "validate",
                "capability_id": "core:validate-deployment",
                "inputs": {"target": "{target}", "workspace": "{workspace}"},
            },
            {
                "id": "deploy",
                "capability_id": "{target}:deploy",
                "inputs": {
                    "target": "{target}",
                    "workspace": "{workspace}",
                    "version": "{version}",
                },
                "retry_policy": {"max_attempts": 3, "initial_delay": 2},
                "compensation_policy": {
                    "compensation_node_id": "rollback",
                    "on_failure": "COMPENSATE",
                },
            },
            {
                "id": "verify",
                "capability_id": "{target}:health-check",
                "inputs": {"target": "{target}", "workspace": "{workspace}"},
            },
            {
                "id": "rollback",
                "capability_id": "{target}:rollback",
                "inputs": {"target": "{target}", "workspace": "{workspace}", "version": "{version}"},
            },
        ],
        dependencies=[
            {"from": "validate", "to": "deploy"},
            {"from": "deploy", "to": "verify"},
        ],
        metadata={"version": "1.0", "author": "sam-builtin"},
    )


def _tmpl_scale_cluster() -> GraphTemplate:
    """Template for scaling a cluster up or down."""
    return GraphTemplate(
        id="tmpl-scale-cluster",
        intent_type=IntentType.SCALE,
        name="Scale Cluster",
        description=(
            "Assess current capacity, calculate target node count, "
            "request approval, scale the cluster, and verify stability."
        ),
        nodes=[
            {
                "id": "assess",
                "capability_id": "cluster:assess-capacity",
                "inputs": {"cluster": "{target}"},
            },
            {
                "id": "calculate",
                "capability_id": "cluster:calculate-target",
                "inputs": {
                    "current": "{assess.output}",
                    "direction": "{direction}",
                    "count": "{count}",
                },
            },
            {
                "id": "scale",
                "capability_id": "{target}:scale",
                "inputs": {"target": "{target}", "nodes": "{calculate.output}"},
                "retry_policy": {"max_attempts": 1},
                "compensation_policy": {
                    "compensation_node_id": "revert-scale",
                    "on_failure": "COMPENSATE",
                },
            },
            {
                "id": "revert-scale",
                "capability_id": "{target}:scale",
                "inputs": {"target": "{target}", "revert": True},
            },
            {
                "id": "stabilise",
                "capability_id": "cluster:wait-stable",
                "inputs": {"target": "{target}", "timeout": 300},
                "retry_policy": {"max_attempts": 10, "initial_delay": 5, "backoff": "LINEAR"},
            },
        ],
        dependencies=[
            {"from": "assess", "to": "calculate"},
            {"from": "calculate", "to": "scale"},
            {"from": "scale", "to": "stabilise"},
        ],
        metadata={"version": "1.0", "author": "sam-builtin", "requires_approval": True},
    )


def _tmpl_optimize_target() -> GraphTemplate:
    """Template for optimising a target's performance."""
    return GraphTemplate(
        id="tmpl-optimize-target",
        intent_type=IntentType.OPTIMIZE,
        name="Optimize Target",
        description="Profile current state, identify bottlenecks, apply optimizations, and benchmark the result.",
        nodes=[
            {
                "id": "profile",
                "capability_id": "{target}:profile",
                "inputs": {"target": "{target}"},
            },
            {
                "id": "analyse",
                "capability_id": "core:analyse-bottlenecks",
                "inputs": {"profile": "{profile.output}", "target": "{target}"},
            },
            {
                "id": "optimize",
                "capability_id": "{target}:apply-optimizations",
                "inputs": {
                    "target": "{target}",
                    "bottlenecks": "{analyse.output}",
                    "threshold": "{threshold}",
                },
                "retry_policy": {"max_attempts": 2},
                "compensation_policy": {
                    "compensation_node_id": "revert-opt",
                    "on_failure": "COMPENSATE",
                },
            },
            {
                "id": "revert-opt",
                "capability_id": "{target}:revert-optimizations",
                "inputs": {"target": "{target}"},
            },
            {
                "id": "benchmark",
                "capability_id": "{target}:benchmark",
                "inputs": {
                    "target": "{target}",
                    "baseline": "{profile.output}",
                },
            },
        ],
        dependencies=[
            {"from": "profile", "to": "analyse"},
            {"from": "analyse", "to": "optimize"},
            {"from": "optimize", "to": "benchmark"},
        ],
        metadata={"version": "1.0", "author": "sam-builtin"},
    )


# ── Built-in Template Library ─────────────────────────────────────────


BUILTIN_TEMPLATES: Dict[IntentType, GraphTemplate] = {
    IntentType.DIAGNOSE: _tmpl_diagnose_runtime(),
    IntentType.REPAIR: _tmpl_repair_provider(),
    IntentType.DEPLOY: _tmpl_deploy_workspace(),
    IntentType.SCALE: _tmpl_scale_cluster(),
    IntentType.OPTIMIZE: _tmpl_optimize_target(),
}


def get_default_template(intent_type: IntentType) -> Optional[GraphTemplate]:
    """Return the built-in template for a given intent type, or None if not found."""
    return BUILTIN_TEMPLATES.get(intent_type)
