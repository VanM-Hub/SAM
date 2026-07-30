"""Delegation DTOs."""
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass(frozen=True)
class DelegationRule:
    rule_id:str=""; from_user:str=""; to_user:str=""; reason:str=""; active:bool=True
    def to_dict(self)->Dict[str,Any]:return {"rule_id":self.rule_id,"from":self.from_user,"to":self.to_user,"reason":self.reason,"active":self.active}

@dataclass(frozen=True)
class DelegationRegistryState:
    rules:List[DelegationRule]=field(default_factory=list)
    def to_dict(self)->Dict[str,Any]:return {"rules":[r.to_dict() for r in self.rules],"count":len(self.rules)}
