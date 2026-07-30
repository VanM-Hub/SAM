"""Delegation Dashboard Bridge."""
from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

@dataclass(frozen=True)
class DelegationCard:
    total:int; active:int; timestamp:float
    def to_dict(self)->Dict[str,Any]:return {"card":"Delegation","total":self.total,"active":self.active,"timestamp":self.timestamp}

class DashboardDelegationBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def card_count(self)->int:return 1
    @property
    def _engine(self):return self._runtime._delegation_engine
    def get_card(self)->DelegationCard:return DelegationCard(total=self._engine.rule_count,active=len(self._engine.list_active()),timestamp=datetime.now().timestamp())
