"""
Guardian Consistency Verifier.

Verifies consistency of justification data.
Rule-based. No AI.
"""

from typing import List
from dataclasses import dataclass, field

from .justification import DecisionJustification


@dataclass(frozen=True)
class ConsistencyResult:
    is_consistent: bool = False
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: float = 1.0
    def to_dict(self) -> dict:
        return {"is_consistent":self.is_consistent,"issues":list(self.issues),"warnings":list(self.warnings),"score":self.score}


class ConsistencyVerifier:
    """Verifies consistency of justifications."""

    def verify(self, justification: DecisionJustification) -> ConsistencyResult:
        issues = []
        warnings = []

        # Missing evidence
        total_evidence = sum(len(s.evidence) for s in justification.sections)
        if total_evidence == 0:
            issues.append("No evidence in any section")

        # Missing rules
        total_rules = sum(len(s.rules) for s in justification.sections)
        if total_rules == 0:
            warnings.append("No rule traces in justification")

        # Missing sections
        if len(justification.sections) < 2:
            warnings.append("Fewer than 2 sections in justification")

        # Orphan (no source)
        if not justification.source_intent_id and not justification.decision_input_id:
            issues.append("Orphan justification: no source references")

        # Empty summary
        if not justification.summary:
            warnings.append("Empty justification summary")

        is_consistent = len(issues) == 0
        score = max(0.0, 1.0 - (len(issues) * 0.3 + len(warnings) * 0.1))

        return ConsistencyResult(is_consistent=is_consistent, issues=issues, warnings=warnings, score=round(score, 2))
