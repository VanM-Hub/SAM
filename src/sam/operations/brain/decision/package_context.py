"""
Decision Runtime Context Builder.

Builds DecisionContext from IncomingDecisionPackage.
Rule-based. Deterministic. No domain knowledge.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .package_protocol import IncomingDecisionPackage


@dataclass(frozen=True)
class DecisionContext:
    context_id: str = ""
    package_id: str = ""
    priority: int = 0
    confidence: float = 0.0
    runtime_ids: List[str] = field(default_factory=list)
    action_type: str = ""
    evidence_count: int = 0
    has_justification: bool = False
    is_ready: bool = False
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"context_id":self.context_id,"package_id":self.package_id,"priority":self.priority,
                "confidence":self.confidence,"runtime_ids":list(self.runtime_ids),"action_type":self.action_type,
                "evidence_count":self.evidence_count,"has_justification":self.has_justification,
                "is_ready":self.is_ready,"summary":self.summary}


class DecisionContextBuilder:
    """Builds DecisionContext from IncomingDecisionPackage."""

    def build(self, package: IncomingDecisionPackage) -> DecisionContext:
        import uuid
        priority = 0
        confidence = 0.0
        action_type = "unknown"
        runtime_ids = []
        evidence_count = 0

        body = package.body
        if body and body.decision_input:
            di = body.decision_input
            priority = di.get("priority_score", 0)
            confidence = di.get("confidence", 0.0)
            candidates = di.get("candidates", [])
            evidence_count = di.get("candidates", [])
            if isinstance(evidence_count, list):
                evidence_count = len(evidence_count)
            for c in candidates:
                if isinstance(c, dict) and c.get("runtime_id"):
                    runtime_ids.append(c["runtime_id"])
                if c.get("action_type"):
                    action_type = c["action_type"]

        return DecisionContext(
            context_id=str(uuid.uuid4()),
            package_id=package.package_id,
            priority=priority,
            confidence=confidence,
            runtime_ids=runtime_ids,
            action_type=action_type,
            evidence_count=evidence_count,
            has_justification=body and bool(body.justification) if body else False,
            is_ready=package.ready and len(package.validation_errors) == 0,
            summary=f"Priority {priority}, Confidence {confidence}, {len(runtime_ids)} runtime(s)",
        )
