# OP-435 — Adapter Validator
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .execution_envelope import ExecutionEnvelope
from .adapter_protocol import ExecutionAdapterProtocol
from .adapter_registry import AdapterRegistry


@dataclass(frozen=True)
class AdapterValidationIssue:
    issue_id: str = ""
    category: str = ""
    severity: str = "warning"
    message: str = ""


@dataclass(frozen=True)
class AdapterValidationReport:
    passed: bool = True
    issues: Tuple[AdapterValidationIssue, ...] = field(default_factory=tuple)
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_blocking(self) -> bool:
        return self.errors > 0


class AdapterValidator:
    """Validates execution envelopes against adapters.

    Validations:
    - adapter_exists
    - protocol_compatible
    - connector_compatible
    - capability_compatible
    - approval_valid
    - guardian_passed
    - dispatch_complete
    """

    def __init__(self, registry: AdapterRegistry) -> None:
        self._registry = registry

    def validate(
        self,
        envelope: ExecutionEnvelope,
        adapter_type: Optional[str] = None,
        approval_valid: bool = False,
        guardian_passed: bool = False,
    ) -> AdapterValidationReport:
        issues: List[AdapterValidationIssue] = []

        # 1. Adapter exists
        at = adapter_type or (envelope.metadata.adapter_type if envelope.metadata else "")
        adapters = self._registry.find_by_type(at) if at else []
        if not adapters:
            issues.append(AdapterValidationIssue(
                category="adapter_exists", severity="error",
                message=f"No adapter found for type '{at}'",
            ))

        # 2. Protocol compatible
        if adapters:
            adapter = adapters[0]
            errors = adapter.validate(envelope)
            if errors:
                issues.append(AdapterValidationIssue(
                    category="protocol_compatible", severity="error",
                    message=f"Protocol errors: {'; '.join(errors)}",
                ))

        # 3. Connector compatible
        if envelope.metadata and envelope.metadata.connector_type:
            if adapters:
                actions = adapters[0].supported_actions()
                for item in envelope.items:
                    if item.action not in actions and actions:
                        issues.append(AdapterValidationIssue(
                            category="connector_compatible", severity="warning",
                            message=f"Action '{item.action}' not in adapter's supported actions",
                        ))

        # 4. Capability compatible
        if envelope.items and adapters:
            adapter = adapters[0]
            meta = adapter.metadata
            cap_names = [c.name for c in meta.capabilities]
            for item in envelope.items:
                item_type = item.adapter_type or ""
                if item_type and item_type not in cap_names:
                    issues.append(AdapterValidationIssue(
                        category="capability_compatible", severity="warning",
                        message=f"Item type '{item_type}' not in adapter capabilities",
                    ))

        # 5. Approval valid
        if envelope.requires_approval and not approval_valid:
            issues.append(AdapterValidationIssue(
                category="approval_valid", severity="error",
                message="Approval required but not validated",
            ))

        # 6. Guardian passed
        if not guardian_passed:
            issues.append(AdapterValidationIssue(
                category="guardian_passed", severity="warning",
                message="Guardian check not confirmed",
            ))

        # 7. Dispatch complete
        if not envelope.items:
            issues.append(AdapterValidationIssue(
                category="dispatch_complete", severity="error",
                message="Envelope has no items",
            ))

        errors = sum(1 for i in issues if i.severity == "error")
        warnings = len(issues) - errors
        passed = errors == 0

        return AdapterValidationReport(
            passed=passed, issues=tuple(issues),
            total_issues=len(issues), errors=errors, warnings=warnings,
        )
