"""
Guardian Live Conversation Justification Bridge.

10 DTO-only query methods for decision justification.
"""

from typing import Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveConversationJustificationBridge:
    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime
    @property
    def query_count(self) -> int: return 10

    def latest_justification(self) -> Dict[str, Any]:
        h = self._runtime.justification_history
        l = h[-1] if h else None
        return {"query":"latest_justification","has_justification":l is not None,
                "justification":l.to_dict() if l else None}

    def show_evidence(self) -> Dict[str, Any]:
        h = self._runtime.justification_history
        l = h[-1] if h else None
        if not l: return {"query":"show_evidence","evidence":[]}
        all_ev = [e.to_dict() for s in l.sections for e in s.evidence]
        return {"query":"show_evidence","total":len(all_ev),"evidence":all_ev}

    def show_rule_trace(self) -> Dict[str, Any]:
        h = self._runtime.justification_history
        l = h[-1] if h else None
        if not l: return {"query":"show_rule_trace","rules":[]}
        all_r = [r.to_dict() for s in l.sections for r in s.rules]
        return {"query":"show_rule_trace","total":len(all_r),"rules":all_r}

    def show_chain(self) -> Dict[str, Any]:
        from .evidence_chain import EvidenceChainBuilder
        h = self._runtime.justification_history
        l = h[-1] if h else None
        if not l: return {"query":"show_chain","complete":False,"steps":[]}
        all_ev = [e for s in l.sections for e in s.evidence]
        chain = EvidenceChainBuilder().build(all_ev)
        return {"query":"show_chain","chain":chain.to_dict()}

    def consistency(self) -> Dict[str, Any]:
        from .consistency import ConsistencyVerifier
        h = self._runtime.justification_history
        l = h[-1] if h else None
        if not l: return {"query":"consistency","consistent":True}
        r = ConsistencyVerifier().verify(l)
        return {"query":"consistency","result":r.to_dict()}

    def summary(self) -> Dict[str, Any]:
        h = self._runtime.justification_history
        return {"query":"summary","total":len(h),"has_latest":len(h)>0}

    def history(self, limit: int = 50) -> Dict[str, Any]:
        h = self._runtime.justification_history
        r = h[-limit:] if limit>0 else h
        return {"query":"history","total":len(h),"returned":len(r),"justifications":[j.to_dict() for j in r]}

    def statistics(self) -> Dict[str, Any]:
        h = self._runtime.justification_history
        total_sec = sum(len(j.sections) for j in h)
        total_ev = sum(len(e) for j in h for s in j.sections for e in s.evidence)
        total_r = sum(len(r) for j in h for s in j.sections for r in s.rules)
        return {"query":"statistics","total":len(h),"total_sections":total_sec,"total_evidence":total_ev,"total_rules":total_r}

    def latest_explanation(self) -> Dict[str, Any]:
        return self.latest_justification()

    def current_justification(self) -> Dict[str, Any]:
        return self.latest_justification()
