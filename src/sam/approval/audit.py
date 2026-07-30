"""Approval Audit DTOs."""
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass(frozen=True)
class AuditEntry:
    entry_id:str=""; action:str=""; actor:str=""; target_id:str=""; detail:str=""; timestamp:float=0.0
    def to_dict(self)->Dict[str,Any]:return {"entry_id":self.entry_id,"action":self.action,"actor":self.actor,"target":self.target_id,"detail":self.detail,"timestamp":self.timestamp}

@dataclass(frozen=True)
class AuditLog:
    entries:List[AuditEntry]=field(default_factory=list)
    def to_dict(self)->Dict[str,Any]:return {"entries":[e.to_dict() for e in self.entries],"count":len(self.entries)}
