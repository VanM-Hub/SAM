# OP-445 — Provider Validator
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .provider_protocol import ExecutionProviderProtocol
from .provider_registry import ProviderRegistry
from sam.execution.adapters.execution_envelope import ExecutionEnvelope


@dataclass(frozen=True)
class ProviderValidationIssue:
    issue_id: str = ""; category: str = ""; severity: str = "warning"; message: str = ""

@dataclass(frozen=True)
class ProviderValidationReport:
    passed: bool = True
    issues: Tuple[ProviderValidationIssue, ...] = field(default_factory=tuple)
    total_issues: int = 0; errors: int = 0; warnings: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    @property
    def has_blocking(self): return self.errors > 0


class ProviderValidator:
    def __init__(self, registry: ProviderRegistry):
        self._registry = registry

    def validate(self, envelope: ExecutionEnvelope, provider_type: str) -> ProviderValidationReport:
        issues: List[ProviderValidationIssue] = []

        providers = self._registry.find_by_type(provider_type)
        if not providers:
            issues.append(ProviderValidationIssue(category="provider_exists",severity="error",
                message=f"No provider for type '{provider_type}'"))

        if providers:
            p = providers[0]
            if not p.metadata.healthy:
                issues.append(ProviderValidationIssue(category="healthy",severity="error",
                    message=f"Provider '{p.metadata.name}' is unhealthy"))

            actions = p.supported_actions()
            for item in envelope.items:
                if item.action not in actions:
                    issues.append(ProviderValidationIssue(category="capability",severity="warning",
                        message=f"Action '{item.action}' not in provider's supported actions"))

        if not envelope.items:
            issues.append(ProviderValidationIssue(category="execution_preview_only",severity="error",
                message="Envelope has no items"))

        errors = sum(1 for i in issues if i.severity=="error")
        warnings = len(issues)-errors
        return ProviderValidationReport(passed=errors==0, issues=tuple(issues),
            total_issues=len(issues), errors=errors, warnings=warnings)
