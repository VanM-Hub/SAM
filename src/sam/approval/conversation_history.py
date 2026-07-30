"""History Conversation Bridge."""
from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

class ConversationHistoryBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def query_count(self)->int:return 6
    @property
    def _engine(self):return self._runtime._history_engine
    def get_history(self,approval_id:str)->Dict[str,Any]:
        h=self._engine.get_history(approval_id)
        return {"query":"history","approval_id":approval_id,"entries":[e.to_dict() for e in h.entries],"count":h.count}
    def get_all(self)->Dict[str,Any]:
        h=self._engine.get_all()
        return {"query":"all_history","entries":[e.to_dict() for e in h.entries],"count":h.count}
    def stats(self)->Dict[str,Any]:return {"query":"history_stats","total":self._engine.entry_count}
