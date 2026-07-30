"""Analytics Dashboard Bridge."""
from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

@dataclass(frozen=True)
class AnalyticsCard:
    metric_count:int; timestamp:float
    def to_dict(self)->Dict[str,Any]:return {"card":"Analytics","metric_count":self.metric_count,"timestamp":self.timestamp}

class DashboardAnalyticsBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def card_count(self)->int:return 1
    @property
    def _engine(self):return self._runtime._analytics_engine
    def get_card(self)->AnalyticsCard:
        return AnalyticsCard(metric_count=self._engine.report().count,timestamp=datetime.now().timestamp())
