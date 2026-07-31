"""Dashboard Runtime Bridge — 5 PolicyCards (Sprint 207)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from ..foundation.policy_registry import PolicyRegistry
from .policy_runtime import PolicyRuntime
from .policy_pipeline import PolicyPipeline
from .policy_engine import PolicyEngine


class DashboardRuntimeBridge:
    """Bridge dashboard — 5 kartu untuk runtime policy."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry
        self._runtime = PolicyRuntime(registry)
        self._pipeline = PolicyPipeline(registry)

    def cards(self):
        n = self._registry.count()
        verdict = "ready" if n > 0 else "empty"
        return [
            PolicyCard("rt.policy", "runtime", verdict,
                       f"{n} policy(s) runnable", "policy runtime", verdict),
            PolicyCard("rt.pipeline", "runtime", "ready",
                       "Descriptor->Policy->Builder->Preview",
                       "pipeline", "ready"),
            PolicyCard("rt.preview", "runtime", "ready",
                       "no decision, external_calls=0", "preview", "ready"),
            PolicyCard("rt.engine", "runtime", "ready",
                       "engine: not LLM, not AI, deterministic", "engine", "ready"),
            PolicyCard("rt.summary", "runtime", "ready",
                       "PolicySummarizer deterministic", "summary", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
