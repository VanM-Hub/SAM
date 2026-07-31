"""Policy Summary — ringkasan policy (Sprint 207)."""
from __future__ import annotations
from dataclasses import dataclass

from ..model.policy import Policy


@dataclass(frozen=True)
class PolicySummary:
    """Ringkasan (immutable)."""
    policy_id: str = ""
    rule_count: int = 0
    scope: str = ""


class PolicySummarizer:
    """Summarizer policy. Deterministik."""

    def summarize(self, policy: Policy) -> PolicySummary:
        return PolicySummary(
            policy_id=policy.policy_id,
            rule_count=policy.rule_count(),
            scope=policy.scope,
        )
