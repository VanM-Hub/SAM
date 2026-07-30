"""Approval Dashboard DTOs."""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass(frozen=True)
class DashboardWidget:
    widget_id:str=""; title:str=""; widget_type:str=""; data:Dict[str,Any]=field(default_factory=dict)
    def to_dict(self)->Dict[str,Any]:return {"widget_id":self.widget_id,"title":self.title,"type":self.widget_type,"data":dict(self.data)}

@dataclass(frozen=True)
class DashboardLayout:
    layout_id:str=""; name:str=""; widgets:List[DashboardWidget]=field(default_factory=list)
    def to_dict(self)->Dict[str,Any]:return {"layout_id":self.layout_id,"name":self.name,"widgets":[w.to_dict() for w in self.widgets]}
