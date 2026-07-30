"""Multi-Level Dashboard Bridge."""
from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

@dataclass(frozen=True)
class LevelCard:
    approval_id:str; current_level:str; completed:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]:return {"card":"Level","approval_id":self.approval_id,"current_level":self.current_level,"completed":self.completed,"timestamp":self.timestamp}
@dataclass(frozen=True)
class StatsCard:
    total:int; active:int; completed:int; timestamp:float
    def to_dict(self)->Dict[str,Any]:return {"card":"MultiLevelStats","total":self.total,"active":self.active,"completed":self.completed,"timestamp":self.timestamp}

class DashboardMultiLevelBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def card_count(self)->int:return 2
    @property
    def _engine(self):return self._runtime._multilevel_engine
    def get_state(self)->Dict[str,Any]:return {"total":self._engine.approval_count,"timestamp":datetime.now().timestamp()}
