"""Audit Engine."""
from typing import List,Optional,Dict
from datetime import datetime
from .audit import AuditEntry, AuditLog

class AuditEngine:
    def __init__(self)->None:self._entries:List[AuditEntry]=[];self._counter:int=0
    @property
    def entry_count(self)->int:return len(self._entries)
    def log(self,action:str,actor:str,target_id:str,detail:str="")->AuditEntry:
        self._counter+=1
        e=AuditEntry(entry_id=f"audit_{self._counter}",action=action,actor=actor,target_id=target_id,detail=detail,timestamp=datetime.now().timestamp())
        self._entries.append(e);return e
    def get_log(self)->AuditLog:return AuditLog(entries=list(self._entries))
    def filter_by_action(self,action:str)->List[AuditEntry]:return [e for e in self._entries if e.action==action]
    def filter_by_actor(self,actor:str)->List[AuditEntry]:return [e for e in self._entries if e.actor==actor]
