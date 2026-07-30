"""
Guardian Live Dashboard Justification Bridge.

6 immutable dashboard cards for decision justification.
"""

from typing import Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


@dataclass(frozen=True)
class EvidenceChainCard:
    complete: bool; steps: int; missing: List[str]; timestamp: float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Evidence Chain","complete":self.complete,"steps":self.steps,"missing":list(self.missing),"timestamp":self.timestamp}

@dataclass(frozen=True)
class RuleTraceCard:
    total_rules: int; all_passed: bool; timestamp: float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Rule Trace","total_rules":self.total_rules,"all_passed":self.all_passed,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ConsistencyCard:
    is_consistent: bool; score: float; issues: int; warnings: int; timestamp: float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Consistency","is_consistent":self.is_consistent,"score":self.score,"issues":self.issues,"warnings":self.warnings,"timestamp":self.timestamp}

@dataclass(frozen=True)
class LatestJustificationCard:
    has_justification: bool; summary: str; sections: int; timestamp: float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Latest Justification","has_justification":self.has_justification,"summary":self.summary,"sections":self.sections,"timestamp":self.timestamp}

@dataclass(frozen=True)
class CoverageCard:
    total_sections: int; total_evidence: int; total_rules: int; coverage_pct: float; timestamp: float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Coverage","total_sections":self.total_sections,"total_evidence":self.total_evidence,"total_rules":self.total_rules,"coverage_pct":self.coverage_pct,"timestamp":self.timestamp}

@dataclass(frozen=True)
class JustificationHistoryCard:
    total: int; total_sections: int; total_evidence: int; avg_score: float; timestamp: float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Justification History","total":self.total,"total_sections":self.total_sections,"total_evidence":self.total_evidence,"average_score":self.avg_score,"timestamp":self.timestamp}


class LiveDashboardJustificationBridge:
    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def card_count(self) -> int: return 6

    def get_evidence_chain_card(self) -> EvidenceChainCard:
        from .evidence_chain import EvidenceChainBuilder
        h = self._runtime.justification_history
        l = h[-1] if h else None
        if not l: return EvidenceChainCard(complete=False,steps=0,missing=[],timestamp=datetime.now().timestamp())
        all_ev = [e for s in l.sections for e in s.evidence]
        c = EvidenceChainBuilder().build(all_ev)
        return EvidenceChainCard(complete=c.complete,steps=len(c.steps),missing=c.missing_steps,timestamp=datetime.now().timestamp())

    def get_rule_trace_card(self) -> RuleTraceCard:
        from .rule_trace import RuleTracer
        h = self._runtime.justification_history; l = h[-1] if h else None
        if not l: return RuleTraceCard(total_rules=0,all_passed=True,timestamp=datetime.now().timestamp())
        all_r = [r for s in l.sections for r in s.rules]
        t = RuleTracer().trace(all_r)
        return RuleTraceCard(total_rules=t.total_rules,all_passed=t.all_passed,timestamp=datetime.now().timestamp())

    def get_consistency_card(self) -> ConsistencyCard:
        from .consistency import ConsistencyVerifier
        h = self._runtime.justification_history; l = h[-1] if h else None
        if not l: return ConsistencyCard(is_consistent=True,score=1.0,issues=0,warnings=0,timestamp=datetime.now().timestamp())
        r = ConsistencyVerifier().verify(l)
        return ConsistencyCard(is_consistent=r.is_consistent,score=r.score,issues=len(r.issues),warnings=len(r.warnings),timestamp=datetime.now().timestamp())

    def get_latest_justification_card(self) -> LatestJustificationCard:
        h = self._runtime.justification_history; l = h[-1] if h else None
        return LatestJustificationCard(has_justification=l is not None,summary=l.summary if l else "",sections=len(l.sections) if l else 0,timestamp=datetime.now().timestamp())

    def get_coverage_card(self) -> CoverageCard:
        h = self._runtime.justification_history
        ts = sum(len(j.sections) for j in h); te = sum(len(e) for j in h for s in j.sections for e in s.evidence)
        tr = sum(len(r) for j in h for s in j.sections for r in s.rules)
        cov = round((te+tr)/max(ts*2,1)*100,1) if ts>0 else 0.0
        return CoverageCard(total_sections=ts,total_evidence=te,total_rules=tr,coverage_pct=cov,timestamp=datetime.now().timestamp())

    def get_justification_history_card(self) -> JustificationHistoryCard:
        h = self._runtime.justification_history
        ts = sum(len(j.sections) for j in h); te = sum(len(e) for j in h for s in j.sections for e in s.evidence)
        return JustificationHistoryCard(total=len(h),total_sections=ts,total_evidence=te,avg_score=1.0,timestamp=datetime.now().timestamp())

    def get_all_cards(self) -> Dict[str,Any]:
        return {"evidence_chain":self.get_evidence_chain_card().to_dict(),"rule_trace":self.get_rule_trace_card().to_dict(),
                "consistency":self.get_consistency_card().to_dict(),"latest_justification":self.get_latest_justification_card().to_dict(),
                "coverage":self.get_coverage_card().to_dict(),"history":self.get_justification_history_card().to_dict()}
