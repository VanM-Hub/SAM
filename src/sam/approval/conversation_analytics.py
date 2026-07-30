"""Analytics Conversation Bridge."""
from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

class ConversationAnalyticsBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def query_count(self)->int:return 4
    @property
    def _engine(self):return self._runtime._analytics_engine
    def get_report(self)->Dict[str,Any]:
        r=self._engine.report();return {"query":"analytics_report","metrics":[m.to_dict() for m in r.metrics],"count":r.count}
    def get_metric(self,key:str)->Dict[str,Any]:
        v=self._engine.get(key);return {"query":"get_metric","key":key,"value":v}
