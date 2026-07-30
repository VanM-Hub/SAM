"""
Guardian Decision Justification DTOs.

Immutable DTOs explaining why a DecisionInput was produced.
No AI. Rule-based. Deterministic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class EvidenceReference:
    step: str = ""; source_id: str = ""; source_type: str = ""
    timestamp: float = 0.0; details: Optional[Dict[str, Any]] = None
    def to_dict(self) -> Dict[str, Any]:
        return {"step":self.step,"source_id":self.source_id,"source_type":self.source_type,"timestamp":self.timestamp,"details":self.details}

@dataclass(frozen=True)
class RuleReference:
    rule_name: str = ""; rule_type: str = ""; triggered: bool = False
    input_values: Optional[Dict[str, Any]] = None; output_value: Optional[str] = None
    def to_dict(self) -> Dict[str, Any]:
        return {"rule_name":self.rule_name,"rule_type":self.rule_type,"triggered":self.triggered,"input_values":self.input_values,"output_value":self.output_value}

@dataclass(frozen=True)
class JustificationSection:
    title: str = ""; content: str = ""; evidence: List[EvidenceReference] = field(default_factory=list)
    rules: List[RuleReference] = field(default_factory=list)
    def to_dict(self) -> Dict[str, Any]:
        return {"title":self.title,"content":self.content,"evidence":[e.to_dict() for e in self.evidence],"rules":[r.to_dict() for r in self.rules]}

@dataclass(frozen=True)
class DecisionJustification:
    justification_id: str = ""; timestamp: float = 0.0
    decision_input_id: str = ""; source_intent_id: str = ""
    sections: List[JustificationSection] = field(default_factory=list)
    summary: str = ""
    def to_dict(self) -> Dict[str, Any]:
        return {"justification_id":self.justification_id,"timestamp":self.timestamp,
                "decision_input_id":self.decision_input_id,"source_intent_id":self.source_intent_id,
                "sections":[s.to_dict() for s in self.sections],"summary":self.summary}

@dataclass(frozen=True)
class JustificationSummary:
    total: int = 0; total_sections: int = 0; total_evidence: int = 0
    total_rules: int = 0; period_start: float = 0.0; period_end: float = 0.0
    latest_justification: Optional[DecisionJustification] = None
    def to_dict(self) -> Dict[str, Any]:
        return {"total":self.total,"total_sections":self.total_sections,"total_evidence":self.total_evidence,
                "total_rules":self.total_rules,"period_start":self.period_start,"period_end":self.period_end,
                "latest_justification":self.latest_justification.to_dict() if self.latest_justification else None}

@dataclass(frozen=True)
class JustificationSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0; total: int = 0
    justifications: List[DecisionJustification] = field(default_factory=list)
    summary: Optional[JustificationSummary] = None
    def to_dict(self) -> Dict[str, Any]:
        return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,"total":self.total,
                "justifications":[j.to_dict() for j in self.justifications],"summary":self.summary.to_dict() if self.summary else None}
