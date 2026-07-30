"""
Decision Runtime Conversation Certification Bridge.

10 DTO-only queries for readiness certification.
"""

from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationCertificationBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10

    def certification(self)->Dict[str,Any]:
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        return {"query":"certification","has_certification":c is not None,"certification":c.to_dict() if c else None}

    def decision(self)->Dict[str,Any]:
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        return {"query":"decision","decision":c.decision.name if c else "NONE"}

    def requirements(self)->Dict[str,Any]:
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        return {"query":"requirements","count":len(c.requirements) if c else 0,"met":sum(1 for r in c.requirements if r.met) if c else 0}

    def evidence(self)->Dict[str,Any]:
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        return {"query":"evidence","count":c.evidence_count if c else 0}

    def blockers(self)->Dict[str,Any]:
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        return {"query":"blockers","blocker_count":c.blocker_count if c else 0,"blocked":c.state.name=='BLOCKED' if c else False}

    def history(self,limit:int=50)->Dict[str,Any]:
        h=self._runtime._certification_engine.history if self._runtime._certification_engine else None
        return {"query":"history","total":h.count if h else 0,"records":[r.to_dict() for r in h.get_all()[-limit:]] if h else []}

    def statistics(self)->Dict[str,Any]:
        s=self._runtime._certification_engine.get_statistics() if self._runtime._certification_engine else None
        return {"query":"statistics","stats":s.to_dict() if s else {}}

    def snapshot(self)->Dict[str,Any]:
        s=self._runtime._certification_engine.create_snapshot() if self._runtime._certification_engine else None
        return {"query":"snapshot","snapshot":s.to_dict() if s else {}}

    def validation(self)->Dict[str,Any]:
        from .certification_validator import CertificationValidator
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        if not c: return {"query":"validation","valid":True}
        r=CertificationValidator().validate(c); return {"query":"validation","result":r.to_dict()}

    def summary(self)->Dict[str,Any]:
        return self.statistics()
