"""
Approval Workflow Conversation Bridge.

10 DTO-only queries for workflow runtime.
"""

from typing import Dict,Any,TYPE_CHECKING,List
from .workflow import WorkflowPhase
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1


class ConversationWorkflowBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10

    @property
    def _engine(self):
        return self._runtime._workflow_engine

    def active_workflows(self)->Dict[str,Any]:
        ws=[w.to_dict() for w in self._engine.get_all().values() if WorkflowRules.is_active(w.phase)]
        return {"query":"active_workflows","count":len(ws),"workflows":ws}
    def completed_workflows(self)->Dict[str,Any]:
        ws=[w.to_dict() for w in self._engine.get_all().values() if WorkflowRules.is_terminal(w.phase)]
        return {"query":"completed_workflows","count":len(ws),"workflows":ws}
    def workflow_by_id(self,workflow_id:str)->Dict[str,Any]:
        w=self._engine.get(workflow_id)
        return {"query":"workflow_by_id","found":w is not None,"workflow":w.to_dict() if w else {}}
    def transition_history(self,workflow_id:str)->Dict[str,Any]:
        w=self._engine.get(workflow_id)
        return {"query":"transition_history","history":[h.to_dict() for h in w.history] if w else []}
    def phase_summary(self)->Dict[str,Any]:
        all_w=list(self._engine.get_all().values());return {"query":"phase_summary",
            "total":len(all_w),"phases":{p.name:sum(1 for w in all_w if w.phase==p) for p in WorkflowPhase}}
    def engine_stats(self)->Dict[str,Any]:return {"query":"engine_stats","workflow_count":self._engine.workflow_count}
    def allowed_transitions(self,phase_name:str)->Dict[str,Any]:
        try:p=WorkflowPhase[phase_name]
        except KeyError:return {"query":"allowed_transitions","allowed":[]}
        return {"query":"allowed_transitions","from":phase_name,"allowed":[t.name for t in WorkflowRules.get_allowed_transitions(p)]}
    def terminal_states(self)->Dict[str,Any]:return {"query":"terminal_states","states":[p.name for p in WorkflowPhase if WorkflowRules.is_terminal(p)]}
    def active_states(self)->Dict[str,Any]:return {"query":"active_states","states":[p.name for p in WorkflowPhase if WorkflowRules.is_active(p)]}
    def rules_summary(self)->Dict[str,Any]:return {"query":"rules_summary","transitions":WorkflowRules.summary()}

from .workflow_rules import WorkflowRules
