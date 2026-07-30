"""
Guardian Rule Trace.

Traces all rules that produced a DecisionInput.
DTO only. Rule-based.
"""

from typing import List, Optional
from dataclasses import dataclass, field

from .justification import RuleReference


@dataclass(frozen=True)
class RuleStep:
    name: str = ""; category: str = ""; result: str = ""
    def to_dict(self) -> dict:
        return {"name":self.name,"category":self.category,"result":self.result}

@dataclass(frozen=True)
class RuleTrace:
    trace_id: str = ""; total_rules: int = 0; all_passed: bool = False
    steps: List[RuleStep] = field(default_factory=list)
    def to_dict(self) -> dict:
        return {"trace_id":self.trace_id,"total_rules":self.total_rules,"all_passed":self.all_passed,"steps":[s.to_dict() for s in self.steps]}


class RuleTracer:
    """Traces rules that produced a DecisionInput."""

    def trace(self, references: List[RuleReference]) -> RuleTrace:
        """Build a rule trace from rule references."""
        import uuid
        steps = [RuleStep(name=r.rule_name,category=r.rule_type,result=r.output_value or "applied") for r in references]
        return RuleTrace(
            trace_id=str(uuid.uuid4()),
            total_rules=len(steps),
            all_passed=all(r.triggered for r in references),
            steps=steps,
        )
