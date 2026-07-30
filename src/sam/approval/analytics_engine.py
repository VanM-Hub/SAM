"""Analytics Engine."""
from typing import List, Dict, Any
from datetime import datetime
from .analytics import AnalyticsMetric, AnalyticsReport

class AnalyticsEngine:
    def __init__(self)->None:self._data:Dict[str,Any]={}
    def record(self,key:str,value:float)->None:self._data[key]=value
    def report(self)->AnalyticsReport:
        m=[AnalyticsMetric(name=k,value=v,unit="count") for k,v in self._data.items()]
        return AnalyticsReport(metrics=m)
    def get(self,key:str)->float:return self._data.get(key,0.0)
