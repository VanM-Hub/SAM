"""History Engine."""
from typing import List, Optional, Dict
from datetime import datetime
from .history import HistoryEntry, ApprovalHistory

class HistoryEngine:
    def __init__(self)->None:self._entries:List[HistoryEntry]=[];self._counter:int=0
    @property
    def entry_count(self)->int:return len(self._entries)
    def record(self,approval_id:str,phase:str,actor:str,reason:str="")->HistoryEntry:
        self._counter+=1
        e=HistoryEntry(entry_id=f"hist_{self._counter}",approval_id=approval_id,phase=phase,actor=actor,reason=reason,timestamp=datetime.now().timestamp())
        self._entries.append(e);return e
    def get_history(self,approval_id:str)->ApprovalHistory:
        es=[e for e in self._entries if e.approval_id==approval_id]
        return ApprovalHistory(entries=es)
    def get_all(self)->ApprovalHistory:return ApprovalHistory(entries=list(self._entries))
