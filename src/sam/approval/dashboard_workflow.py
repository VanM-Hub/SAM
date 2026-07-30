"""
Approval Workflow Dashboard Bridge.

6 immutable cards for workflow runtime.
"""

from typing import Dict,Any,TYPE_CHECKING,List
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1


@dataclass(frozen=True)
class WorkflowCard:
    workflow_id:str; phase:str; owner:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Workflow","workflow_id":self.workflow_id,"phase":self.phase,"owner":self.owner,"timestamp":self.timestamp}

@dataclass(frozen=True)
class PhaseDistributionCard:
    phases:Dict[str,int]; total:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"PhaseDistribution","phases":self.phases,"total":self.total,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ActiveWorkflowsCard:
    count:int; active:List[str]; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"ActiveWorkflows","count":self.count,"active":self.active,"timestamp":self.timestamp}

@dataclass(frozen=True)
class CompletedWorkflowsCard:
    count:int; completed:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"CompletedWorkflows","count":self.count,"completed":self.completed,"timestamp":self.timestamp}

@dataclass(frozen=True)
class EngineCard:
    workflow_count:int; has_workflows:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Engine","workflow_count":self.workflow_count,"has_workflows":self.has_workflows,"timestamp":self.timestamp}

@dataclass(frozen=True)
class SummaryCard:
    total:int; active:int; terminal:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Summary","total":self.total,"active":self.active,"terminal":self.terminal,"timestamp":self.timestamp}


class DashboardWorkflowBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None: self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    @property
    def _engine(self): return self._runtime._workflow_engine

    def get_workflow_card(self,workflow_id:str)->WorkflowCard:
        w=self._engine.get(workflow_id)
        return WorkflowCard(workflow_id=w.workflow_id if w else "",phase=w.phase.name if w else "NONE",
            owner=w.owner if w else "",timestamp=datetime.now().timestamp())
    def get_distribution_card(self)->PhaseDistributionCard:
        all_w=list(self._engine.get_all().values())
        return PhaseDistributionCard(phases={p.name:sum(1 for w in all_w if w.phase==p) for p in WorkflowPhase},
            total=len(all_w),timestamp=datetime.now().timestamp())
    def get_active_card(self)->ActiveWorkflowsCard:
        ws=[w.workflow_id for w in self._engine.get_all().values() if WorkflowRules.is_active(w.phase)]
        return ActiveWorkflowsCard(count=len(ws),active=ws,timestamp=datetime.now().timestamp())
    def get_completed_card(self)->CompletedWorkflowsCard:
        ws=[w.workflow_id for w in self._engine.get_all().values() if WorkflowRules.is_terminal(w.phase)]
        return CompletedWorkflowsCard(count=len(ws),completed=len(ws),timestamp=datetime.now().timestamp())
    def get_engine_card(self)->EngineCard:
        return EngineCard(workflow_count=self._engine.workflow_count,
            has_workflows=self._engine.workflow_count>0,timestamp=datetime.now().timestamp())
    def get_summary_card(self)->SummaryCard:
        all_w=list(self._engine.get_all().values());a=sum(1 for w in all_w if WorkflowRules.is_active(w.phase))
        t=sum(1 for w in all_w if WorkflowRules.is_terminal(w.phase))
        return SummaryCard(total=len(all_w),active=a,terminal=t,timestamp=datetime.now().timestamp())
    def get_all_cards(self)->Dict[str,Any]:
        return {"engine":self.get_engine_card().to_dict(),"distribution":self.get_distribution_card().to_dict(),
                "active":self.get_active_card().to_dict(),"completed":self.get_completed_card().to_dict(),
                "summary":self.get_summary_card().to_dict()}

from . import WorkflowPhase as WorkflowPhase
from .workflow_rules import WorkflowRules
