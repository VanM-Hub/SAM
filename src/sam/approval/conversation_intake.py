"""
Approval Runtime Conversation Intake Bridge.

10 DTO-only queries for intake runtime.
"""

from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1


class ConversationIntakeBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10

    def latest_intake(self)->Dict[str,Any]:
        l=self._runtime._registry.latest if self._runtime._registry else None
        return {"query":"latest_intake","has_intake":l is not None,"record":l.to_dict() if l else None}

    def intake_status(self)->Dict[str,Any]:
        l=self._runtime._registry.latest if self._runtime._registry else None
        return {"query":"intake_status","has_status":l is not None,"record_id":l.record_id if l else "NONE"}

    def validation_findings(self)->Dict[str,Any]:
        v=self._runtime._last_validation
        return {"query":"validation_findings","errors":list(v.errors) if v else [],"valid":v.valid if v else True}

    def warnings(self)->Dict[str,Any]:
        v=self._runtime._last_validation
        return {"query":"warnings","warnings":list(v.warnings) if v else []}

    def readiness(self)->Dict[str,Any]:
        s=self._runtime._last_summary
        return {"query":"readiness","readiness":s.readiness if s else "UNKNOWN","score":s.readiness_score if s else 0.0}

    def duplicates(self)->Dict[str,Any]:
        return {"query":"duplicates","count":self._runtime._registry.duplicates if self._runtime._registry else 0}

    def registry_stats(self)->Dict[str,Any]:
        return {"query":"registry_stats","count":self._runtime._registry.count if self._runtime._registry else 0}

    def categories(self)->Dict[str,Any]:
        return {"query":"categories","available":["manual","decision","api","system","general"]}

    def sources(self)->Dict[str,Any]:
        return {"query":"sources","available":["MANUAL","DECISION_RUNTIME","API","SYSTEM"]}

    def summary(self)->Dict[str,Any]:
        s=self._runtime._last_summary
        return {"query":"summary","summary":s.to_dict() if s else {}}
