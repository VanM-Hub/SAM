"""Delegation Engine."""
from typing import List, Optional, Dict
from .delegation import DelegationRule, DelegationRegistryState

class DelegationEngine:
    def __init__(self)->None:self._rules:Dict[str,DelegationRule]={}
    @property
    def rule_count(self)->int:return len(self._rules)
    def add(self,rule:DelegationRule)->None:self._rules[rule.rule_id]=rule
    def get(self,rule_id:str)->Optional[DelegationRule]:return self._rules.get(rule_id)
    def resolve(self,user:str)->str:
        for r in self._rules.values():
            if r.from_user==user and r.active:return r.to_user
        return user
    def deactivate(self,rule_id:str)->None:
        r=self._rules.get(rule_id)
        if r:self._rules[rule_id]=DelegationRule(rule_id=r.rule_id,from_user=r.from_user,to_user=r.to_user,reason=r.reason,active=False)
    def list_active(self)->List[DelegationRule]:return [r for r in self._rules.values() if r.active]
    def list_all(self)->List[DelegationRule]:return list(self._rules.values())
