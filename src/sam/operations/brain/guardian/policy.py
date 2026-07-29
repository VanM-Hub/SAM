"""
OP-312 — OperationalPolicy Engine

Policy untuk guardian:
  - approval required
  - minimum confidence
  - trust threshold
  - mandatory evidence
  - critical escalation
  - provider restriction
  - mission restriction
  - workspace restriction

Policy immutable.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class PolicyRule:
    name: str
    description: str
    category: str  # approval, confidence, trust, evidence, escalation, provider, mission, workspace
    enabled: bool = True
    parameters: Tuple[Tuple[str, Any], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "enabled": self.enabled,
            "parameters": [(k, str(v)) for k, v in self.parameters],
        }


@dataclass(frozen=True)
class PolicyViolation:
    rule_name: str
    category: str
    severity: str  # info, warning, critical
    message: str
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True)
class PolicyResult:
    passed: bool
    violations: Tuple[PolicyViolation, ...] = ()
    warnings: Tuple[PolicyViolation, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [v.to_dict() for v in self.warnings],
        }


class OperationalPolicyEngine:
    """
    Policy engine untuk guardian.
    Semua policy immutable.
    """

    # ── Default policies ──────────────────────────────────────────

    @staticmethod
    def default_policies() -> Tuple[PolicyRule, ...]:
        return (
            PolicyRule(
                name="approval_required_for_high_risk",
                description="Keputusan high/critical risk memerlukan approval",
                category="approval",
                parameters=(("risk_levels", "high,critical"),),
            ),
            PolicyRule(
                name="minimum_confidence",
                description="Minimum confidence score untuk keputusan",
                category="confidence",
                parameters=(("min_score", "0.4"),),
            ),
            PolicyRule(
                name="trust_threshold",
                description="Minimum trust level untuk auto-approve",
                category="trust",
                parameters=(("min_trust", "0.7"),),
            ),
            PolicyRule(
                name="mandatory_evidence",
                description="Setiap proposal minimal memiliki evidence",
                category="evidence",
                parameters=(("min_evidence_count", "1"),),
            ),
            PolicyRule(
                name="critical_escalation",
                description="Keputusan critical harus melewati eskalasi",
                category="escalation",
                parameters=(("escalation_level", "manual_review"),),
            ),
            PolicyRule(
                name="no_provider_bypass",
                description="Tidak boleh bypass provider saat reasoning",
                category="provider",
                parameters=(("bypass_allowed", "false"),),
            ),
            PolicyRule(
                name="mission_state_check",
                description="Mission harus dalam state yang valid untuk eksekusi",
                category="mission",
                parameters=(("allowed_states", "READY,RUNNING"),),
            ),
            PolicyRule(
                name="workspace_isolation",
                description="Workspace harus terisolasi untuk eksekusi",
                category="workspace",
                parameters=(("isolation_required", "true"),),
            ),
        )

    def __init__(self, policies: Optional[Tuple[PolicyRule, ...]] = None):
        self._policies = policies or self.default_policies()

    @property
    def policies(self) -> Tuple[PolicyRule, ...]:
        return self._policies

    def evaluate(
        self,
        proposal: Any,
        evaluation: Any,
        trust_level: float = 0.0,
        evidence_count: int = 0,
        mission_state: str = "",
        provider_used: bool = False,
        workspace_isolated: bool = False,
    ) -> PolicyResult:
        violations: List[PolicyViolation] = []
        warnings: List[PolicyViolation] = []

        for policy in self._policies:
            if not policy.enabled:
                continue

            if policy.category == "approval":
                self._check_approval(policy, proposal, evaluation, violations, warnings)
            elif policy.category == "confidence":
                self._check_confidence(policy, evaluation, violations, warnings)
            elif policy.category == "trust":
                self._check_trust(policy, trust_level, violations, warnings)
            elif policy.category == "evidence":
                self._check_evidence(policy, evidence_count, violations, warnings)
            elif policy.category == "escalation":
                self._check_escalation(policy, evaluation, violations, warnings)
            elif policy.category == "provider":
                self._check_provider(policy, provider_used, violations, warnings)
            elif policy.category == "mission":
                self._check_mission(policy, mission_state, violations, warnings)
            elif policy.category == "workspace":
                self._check_workspace(policy, workspace_isolated, violations, warnings)

        return PolicyResult(
            passed=len(violations) == 0,
            violations=tuple(violations),
            warnings=tuple(warnings),
        )

    # ── Policy checkers ───────────────────────────────────────────

    def _check_approval(
        self,
        policy: PolicyRule,
        proposal: Any,
        evaluation: Any,
        violations: List[PolicyViolation],
        warnings: List[PolicyViolation],
    ) -> None:
        requires = self._get_policy_param(policy, "risk_levels", "high,critical")
        risk = getattr(evaluation, "risk_level", "low") if evaluation else "low"
        if risk in requires:
            has_approval = getattr(proposal, "requires_approval", False) if proposal else False
            if not has_approval:
                violations.append(PolicyViolation(
                    rule_name=policy.name,
                    category=policy.category,
                    severity="critical",
                    message=f"Risk level '{risk}' requires approval approval, but proposal has none",
                ))

    def _check_confidence(
        self,
        policy: PolicyRule,
        evaluation: Any,
        violations: List[PolicyViolation],
        warnings: List[PolicyViolation],
    ) -> None:
        min_score = float(self._get_policy_param(policy, "min_score", "0.4"))
        confidence = getattr(evaluation, "confidence", 1.0) if evaluation else 1.0
        if confidence < min_score:
            violations.append(PolicyViolation(
                rule_name=policy.name,
                category=policy.category,
                severity="critical",
                message=f"Confidence {confidence:.2f} below minimum {min_score:.2f}",
            ))

    def _check_trust(
        self,
        policy: PolicyRule,
        trust_level: float,
        violations: List[PolicyViolation],
        warnings: List[PolicyViolation],
    ) -> None:
        min_trust = float(self._get_policy_param(policy, "min_trust", "0.7"))
        if trust_level < min_trust:
            warnings.append(PolicyViolation(
                rule_name=policy.name,
                category=policy.category,
                severity="warning",
                message=f"Trust level {trust_level:.2f} below threshold {min_trust:.2f}",
            ))

    def _check_evidence(
        self,
        policy: PolicyRule,
        evidence_count: int,
        violations: List[PolicyViolation],
        warnings: List[PolicyViolation],
    ) -> None:
        min_ev = int(float(self._get_policy_param(policy, "min_evidence_count", "1")))
        if evidence_count < min_ev:
            violations.append(PolicyViolation(
                rule_name=policy.name,
                category=policy.category,
                severity="critical",
                message=f"Evidence count {evidence_count} below minimum {min_ev}",
            ))

    def _check_escalation(
        self,
        policy: PolicyRule,
        evaluation: Any,
        violations: List[PolicyViolation],
        warnings: List[PolicyViolation],
    ) -> None:
        risk = getattr(evaluation, "risk_level", "low") if evaluation else "low"
        if risk == "critical":
            violations.append(PolicyViolation(
                rule_name=policy.name,
                category=policy.category,
                severity="critical",
                message="Critical risk requires manual escalation review",
            ))

    def _check_provider(
        self,
        policy: PolicyRule,
        provider_used: bool,
        violations: List[PolicyViolation],
        warnings: List[PolicyViolation],
    ) -> None:
        bypass_allowed = self._get_policy_param(policy, "bypass_allowed", "false") == "true"
        if not provider_used and not bypass_allowed:
            warnings.append(PolicyViolation(
                rule_name=policy.name,
                category=policy.category,
                severity="warning",
                message="Provider not used during reasoning",
            ))

    def _check_mission(
        self,
        policy: PolicyRule,
        mission_state: str,
        violations: List[PolicyViolation],
        warnings: List[PolicyViolation],
    ) -> None:
        allowed = self._get_policy_param(policy, "allowed_states", "READY,RUNNING")
        allowed_states = [s.strip() for s in allowed.split(",")]
        if mission_state and mission_state not in allowed_states:
            violations.append(PolicyViolation(
                rule_name=policy.name,
                category=policy.category,
                severity="critical",
                message=f"Mission state '{mission_state}' not in allowed states: {allowed}",
            ))

    def _check_workspace(
        self,
        policy: PolicyRule,
        workspace_isolated: bool,
        violations: List[PolicyViolation],
        warnings: List[PolicyViolation],
    ) -> None:
        iso_required = self._get_policy_param(policy, "isolation_required", "true") == "true"
        if iso_required and not workspace_isolated:
            violations.append(PolicyViolation(
                rule_name=policy.name,
                category=policy.category,
                severity="critical",
                message="Workspace isolation required but not active",
            ))

    @staticmethod
    def _get_policy_param(policy: PolicyRule, key: str, default: str = "") -> str:
        for k, v in policy.parameters:
            if k == key:
                return v
        return default
