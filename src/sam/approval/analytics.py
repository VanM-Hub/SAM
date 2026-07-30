"""Approval Analytics DTOs."""
from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass(frozen=True)
class AnalyticsMetric:
    name:str=""; value:float=0.0; unit:str=""
    def to_dict(self)->Dict[str,Any]:return {"name":self.name,"value":self.value,"unit":self.unit}

@dataclass(frozen=True)
class AnalyticsReport:
    metrics:List[AnalyticsMetric]=field(default_factory=list)
    def to_dict(self)->Dict[str,Any]:return {"metrics":[m.to_dict() for m in self.metrics],"count":len(self.metrics)}
