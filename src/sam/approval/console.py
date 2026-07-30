"""Approval Console DTOs."""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass(frozen=True)
class ConsoleCommand:
    command:str=""; args:Dict[str,Any]=field(default_factory=dict); executor:str=""
    def to_dict(self)->Dict[str,Any]:return {"command":self.command,"args":dict(self.args),"executor":self.executor}

@dataclass(frozen=True)
class ConsoleResponse:
    command:str=""; success:bool=False; data:Dict[str,Any]=field(default_factory=dict); error:str=""
    def to_dict(self)->Dict[str,Any]:return {"command":self.command,"success":self.success,"data":dict(self.data),"error":self.error}
