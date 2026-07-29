# OP-385 — Learning Policy Engine
# Python 3.8 compatible, frozen dataclass, synchronous only
# 8 built-in learning policies for filtering/validating recommendations
# All decisions are DTO-based — no side effects

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from .knowledge_base import KnowledgeRecord
from .experience_repository import ExperienceRecord


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PolicyDecision:
    """Decision from a single policy check."""
    policy_name: str = ""
    approved: bool = True
    reason: str = ""
    severity: str = "info"  # info, warning, error
    details: str = ""


@dataclass(frozen=True)
class LearningPolicy:
    """Configuration for a specific learning policy."""
    name: str = ""
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# LearningPolicyEngine
# ---------------------------------------------------------------------------

class LearningPolicyEngine:
    """Evaluates knowledge and recommendations against learning policies.

    8 built-in policies:
    1. minimum_evidence
    2. minimum_confidence
    3. duplicate_suppression
    4. conflict_suppression
    5. stale_knowledge
    6. expired_recommendation
    7. approval_required
    8. guardian_required

    All decisions are DTOs — no mutation of stored data.
    """

    def __init__(self) -> None:
        self._policies: Dict[str, LearningPolicy] = {
            "minimum_evidence": LearningPolicy(
                name="minimum_evidence",
                enabled=True,
                params={"min_evidence_count": 1},
            ),
            "minimum_confidence": LearningPolicy(
                name="minimum_confidence",
                enabled=True,
                params={"min_confidence": 0.1},
            ),
            "duplicate_suppression": LearningPolicy(
                name="duplicate_suppression",
                enabled=True,
                params={},
            ),
            "conflict_suppression": LearningPolicy(
                name="conflict_suppression",
                enabled=True,
                params={},
            ),
            "stale_knowledge": LearningPolicy(
                name="stale_knowledge",
                enabled=True,
                params={"max_age_days": 90},
            ),
            "expired_recommendation": LearningPolicy(
                name="expired_recommendation",
                enabled=True,
                params={"expire_days": 30},
            ),
            "approval_required": LearningPolicy(
                name="approval_required",
                enabled=True,
                params={"threshold_confidence": 0.8},
            ),
            "guardian_required": LearningPolicy(
                name="guardian_required",
                enabled=True,
                params={"threshold_confidence": 0.9},
            ),
        }

    # --- Policy Configuration ---

    def get_policy(self, name: str) -> Optional[LearningPolicy]:
        return self._policies.get(name)

    def set_policy_params(self, name: str, params: Dict[str, Any]) -> bool:
        """Update parameters of an existing policy."""
        policy = self._policies.get(name)
        if policy is None:
            return False
        merged = dict(policy.params)
        merged.update(params)
        self._policies[name] = LearningPolicy(
            name=policy.name,
            enabled=policy.enabled,
            params=merged,
        )
        return True

    def enable_policy(self, name: str, enabled: bool) -> bool:
        policy = self._policies.get(name)
        if policy is None:
            return False
        self._policies[name] = LearningPolicy(
            name=policy.name,
            enabled=enabled,
            params=policy.params,
        )
        return True

    def list_policies(self) -> Tuple[LearningPolicy, ...]:
        return tuple(self._policies.values())

    # --- Evaluation Methods ---

    def evaluate_record(self, record: KnowledgeRecord) -> Tuple[PolicyDecision, ...]:
        """Evaluate a single knowledge record against all active policies."""
        decisions: List[PolicyDecision] = []

        for policy in self._policies.values():
            if not policy.enabled:
                continue

            decision = self._apply_policy(policy, record=record)
            decisions.append(decision)

        return tuple(decisions)

    def evaluate_records(
        self, records: Tuple[KnowledgeRecord, ...]
    ) -> Dict[str, Tuple[PolicyDecision, ...]]:
        """Evaluate all records against active policies."""
        results: Dict[str, Tuple[PolicyDecision, ...]] = {}
        for rec in records:
            results[rec.record_id] = self.evaluate_record(rec)
        return results

    def evaluate_recommendation(
        self,
        category: str,
        fact: str,
        confidence: float,
        evidence_count: int,
        existing_records: Tuple[KnowledgeRecord, ...] = (),
    ) -> Tuple[PolicyDecision, ...]:
        """Evaluate a proposed learning recommendation."""
        decisions: List[PolicyDecision] = []

        for policy in self._policies.values():
            if not policy.enabled:
                continue

            decision = self._apply_policy(
                policy,
                category=category,
                fact=fact,
                confidence=confidence,
                evidence_count=evidence_count,
                existing_records=existing_records,
            )
            decisions.append(decision)

        return tuple(decisions)

    # --- Internal Policy Application ---

    def _apply_policy(
        self,
        policy: LearningPolicy,
        record: Optional[KnowledgeRecord] = None,
        category: str = "",
        fact: str = "",
        confidence: float = 0.0,
        evidence_count: int = 0,
        existing_records: Tuple[KnowledgeRecord, ...] = (),
    ) -> PolicyDecision:
        """Apply a single policy and return its decision."""
        name = policy.name
        params = policy.params
        now = datetime.utcnow()

        if name == "minimum_evidence":
            min_ev = params.get("min_evidence_count", 1)
            actual = record.evidence_count if record else evidence_count
            if actual < min_ev:
                return PolicyDecision(
                    policy_name=name,
                    approved=False,
                    reason=f"Evidence count ({actual}) below minimum ({min_ev})",
                    severity="warning",
                )
            return PolicyDecision(
                policy_name=name,
                approved=True,
                reason=f"Evidence count ({actual}) meets minimum ({min_ev})",
            )

        if name == "minimum_confidence":
            min_conf = params.get("min_confidence", 0.1)
            actual = record.confidence if record else confidence
            if actual < min_conf:
                return PolicyDecision(
                    policy_name=name,
                    approved=False,
                    reason=f"Confidence ({actual:.3f}) below minimum ({min_conf})",
                    severity="warning",
                )
            return PolicyDecision(
                policy_name=name,
                approved=True,
                reason=f"Confidence ({actual:.3f}) meets minimum ({min_conf})",
            )

        if name == "duplicate_suppression":
            if record:
                for existing in existing_records:
                    if (existing.record_id != record.record_id
                            and existing.fact.lower().strip() == record.fact.lower().strip()):
                        return PolicyDecision(
                            policy_name=name,
                            approved=False,
                            reason=f"Duplicate of record {existing.record_id[:8]}",
                            severity="warning",
                        )
            else:
                for existing in existing_records:
                    if existing.fact.lower().strip() == fact.lower().strip():
                        return PolicyDecision(
                            policy_name=name,
                            approved=False,
                            reason=f"Duplicate of existing record {existing.record_id[:8]}",
                            severity="warning",
                        )
            return PolicyDecision(
                policy_name=name,
                approved=True,
                reason="No duplicate detected",
            )

        if name == "conflict_suppression":
            if record:
                for existing in existing_records:
                    if (existing.record_id != record.record_id
                            and existing.category == record.category
                            and existing.fact.lower().strip() != record.fact.lower().strip()):
                        return PolicyDecision(
                            policy_name=name,
                            approved=True,  # allow but flag
                            reason=f"Potential conflict with {existing.record_id[:8]}",
                            severity="info",
                        )
            else:
                for existing in existing_records:
                    if (existing.category == category
                            and existing.fact.lower().strip() != fact.lower().strip()):
                        return PolicyDecision(
                            policy_name=name,
                            approved=True,
                            reason=f"Potential conflict with {existing.record_id[:8]}",
                            severity="info",
                        )
            return PolicyDecision(
                policy_name=name,
                approved=True,
                reason="No conflict detected",
            )

        if name == "stale_knowledge":
            if record is None:
                return PolicyDecision(
                    policy_name=name,
                    approved=True,
                    reason="No record to check",
                )
            max_age = timedelta(days=params.get("max_age_days", 90))
            age = now - record.created_at
            if age > max_age:
                return PolicyDecision(
                    policy_name=name,
                    approved=False,
                    reason=f"Knowledge is stale (age={age.days}d, max={max_age.days}d)",
                    severity="warning",
                )
            return PolicyDecision(
                policy_name=name,
                approved=True,
                reason=f"Knowledge is fresh (age={age.days}d)",
            )

        if name == "expired_recommendation":
            if record is None:
                return PolicyDecision(
                    policy_name=name,
                    approved=True,
                    reason="No record to check",
                )
            expire_days = params.get("expire_days", 30)
            max_age = timedelta(days=expire_days)
            age = now - record.created_at
            if age > max_age:
                return PolicyDecision(
                    policy_name=name,
                    approved=False,
                    reason=f"Recommendation expired (age={age.days}d, max={expire_days}d)",
                    severity="error",
                )
            return PolicyDecision(
                policy_name=name,
                approved=True,
                reason=f"Recommendation valid (age={age.days}d)",
            )

        if name == "approval_required":
            threshold = params.get("threshold_confidence", 0.8)
            actual = record.confidence if record else confidence
            if actual >= threshold:
                return PolicyDecision(
                    policy_name=name,
                    approved=False,
                    reason=f"High confidence ({actual:.3f} >= {threshold}) requires approval",
                    severity="info",
                )
            return PolicyDecision(
                policy_name=name,
                approved=True,
                reason=f"Confidence ({actual:.3f}) below approval threshold ({threshold})",
            )

        if name == "guardian_required":
            threshold = params.get("threshold_confidence", 0.9)
            actual = record.confidence if record else confidence
            if actual >= threshold:
                return PolicyDecision(
                    policy_name=name,
                    approved=False,
                    reason=f"Very high confidence ({actual:.3f} >= {threshold}) requires guardian review",
                    severity="warning",
                )
            return PolicyDecision(
                policy_name=name,
                approved=True,
                reason=f"Confidence ({actual:.3f}) below guardian threshold ({threshold})",
            )

        return PolicyDecision(
            policy_name=name,
            approved=True,
            reason=f"Unknown policy '{name}', passing by default",
        )
