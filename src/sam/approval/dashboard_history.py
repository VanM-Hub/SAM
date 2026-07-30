"""History Dashboard Bridge."""
from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

@dataclass(frozen=True)
class HistoryCard:
    total:int; timestamp:float
    def to_dict(self)->Dict[str,Any]:return {"card":"History","total":self.total,"timestamp":self.timestamp}

class DashboardHistoryBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def card_count(self)->int:return 1
    @property
    def _engine(self):return self._runtime._history_engine
    def get_card(self)->HistoryCard:return HistoryCard(total=self._engine.entry_count,timestamp=datetime.now().timestamp())
