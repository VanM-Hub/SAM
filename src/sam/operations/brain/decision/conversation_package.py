"""
Decision Runtime Conversation Package Bridge.

10 DTO-only query methods for package consumption.
"""

from typing import Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3


class DecisionConversationPackageBridge:
    def __init__(self, runtime: "DecisionRuntimeV3") -> None:
        self._runtime = runtime
    @property
    def query_count(self) -> int: return 10

    def latest_package(self) -> Dict[str,Any]:
        l = self._runtime._latest_incoming
        return {"query":"latest_package","has_package":l is not None,"package":l.to_dict() if l else None}

    def validation(self) -> Dict[str,Any]:
        l = self._runtime._latest_validation
        return {"query":"validation","result":l.to_dict() if l else {"valid":True}}

    def normalized(self) -> Dict[str,Any]:
        l = self._runtime._latest_normalized
        return {"query":"normalized","has_normalized":l is not None,"package":l.to_dict() if l else None}

    def context(self) -> Dict[str,Any]:
        l = self._runtime._latest_context
        return {"query":"context","has_context":l is not None,"context":l.to_dict() if l else None}

    def statistics(self) -> Dict[str,Any]:
        return {"query":"statistics","total_consumed":self._runtime._consume_count,"total_valid":self._runtime._valid_count}

    def version(self) -> Dict[str,Any]:
        return {"query":"version","supported_versions":["1.0"],"current_version":"1.0"}

    def summary(self) -> Dict[str,Any]:
        return {"query":"summary","consumed":self._runtime._consume_count,"valid":self._runtime._valid_count,
                "has_context":self._runtime._latest_context is not None}

    def history(self, limit:int=50) -> Dict[str,Any]:
        return {"query":"history","total":self._runtime._consume_count,"limited_to":limit}

    def errors(self) -> Dict[str,Any]:
        l = self._runtime._latest_validation
        return {"query":"errors","errors":l.errors if l else [],"total":len(l.errors) if l else 0}

    def readiness(self) -> Dict[str,Any]:
        l = self._runtime._latest_context
        return {"query":"readiness","ready":l.is_ready if l else False,"package_count":self._runtime._consume_count}
