"""Approval History DTOs."""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from .workflow import WorkflowPhase

@dataclass(frozen=True)
class HistoryEntry:
    entry_id:str=""; approval_id:str=""; phase:str=""; actor:str=""; reason:str=""; timestamp:float=0.0
    def to_dict(self)->Dict[str,Any]:return {"entry_id":self.entry_id,"approval_id":self.approval_id,"phase":self.phase,"actor":self.actor,"reason":self.reason,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ApprovalHistory:
    entries:List[HistoryEntry]=field(default_factory=list)
    def to_dict(self)->Dict[str,Any]:return {"entries":[e.to_dict() for e in self.entries],"count":len(self.entries)}
