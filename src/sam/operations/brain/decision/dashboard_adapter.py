"""
Decision Runtime Dashboard Adapter Bridge.

6 immutable cards for approval adapter.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3

@dataclass(frozen=True)
class ApprovalAdapterCard:
    has_envelope:bool; ready:bool; adapter_ok:bool; bridge_count:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Approval Adapter","has_envelope":self.has_envelope,"ready":self.ready,"adapter_ok":self.adapter_ok,"bridge_count":self.bridge_count,"timestamp":self.timestamp}

@dataclass(frozen=True)
class EnvelopeCard:
    has_envelope:bool; has_refs:bool; has_payload:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Envelope","has_envelope":self.has_envelope,"has_references":self.has_refs,"has_payload":self.has_payload,"timestamp":self.timestamp}

@dataclass(frozen=True)
class MappingCard:
    mapped:bool; ready:bool; action_type:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Mapping","mapped":self.mapped,"ready":self.ready,"action_type":self.action_type,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ValidationCard:
    success:bool; score:float; errors:int; warnings:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Validation","success":self.success,"score":self.score,"errors":self.errors,"warnings":self.warnings,"timestamp":self.timestamp}

@dataclass(frozen=True)
class StatusCard:
    state:str; pending:int; approved:int; rejected:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Status","state":self.state,"pending":self.pending,"approved":self.approved,"rejected":self.rejected,"timestamp":self.timestamp}

@dataclass(frozen=True)
class StatisticsCard:
    envelopes:int; mirrors:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","envelopes":self.envelopes,"mirrors":self.mirrors,"timestamp":self.timestamp}


class DecisionDashboardAdapterBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None:
        self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_approval_adapter_card(self)->ApprovalAdapterCard:
        b=self._runtime._bridge; e=b.last_envelope if b else None
        return ApprovalAdapterCard(has_envelope=e is not None,ready=e.ready if e else False,adapter_ok=b.last_result.success if b and b.last_result else False,
            bridge_count=b.bridge_count if b else 0,timestamp=datetime.now().timestamp())

    def get_envelope_card(self)->EnvelopeCard:
        e=self._runtime._bridge.last_envelope if self._runtime._bridge else None
        return EnvelopeCard(has_envelope=e is not None,has_refs=e.references is not None if e else False,
            has_payload=e.payload is not None if e else False,timestamp=datetime.now().timestamp())

    def get_mapping_card(self)->MappingCard:
        e=self._runtime._bridge.last_envelope if self._runtime._bridge else None
        return MappingCard(mapped=e is not None,ready=e.ready if e else False,action_type=e.payload.action_type if e and e.payload else "",
            timestamp=datetime.now().timestamp())

    def get_validation_card(self)->ValidationCard:
        r=self._runtime._bridge.last_result if self._runtime._bridge else None
        return ValidationCard(success=r.success if r else True,score=r.validation_result.get("score",1.0) if r and r.validation_result else 1.0,
            errors=len(r.errors) if r else 0,warnings=len(r.warnings) if r else 0,timestamp=datetime.now().timestamp())

    def get_status_card(self)->StatusCard:
        s=self._runtime._status_store
        sm=s.get_summary() if s else None
        return StatusCard(state=s.latest.state if s else "NONE",pending=sm.pending if sm else 0,approved=sm.approved if sm else 0,
            rejected=sm.rejected if sm else 0,timestamp=datetime.now().timestamp())

    def get_statistics_card(self)->StatisticsCard:
        b=self._runtime._bridge; s=self._runtime._status_store
        return StatisticsCard(envelopes=b.bridge_count if b else 0,mirrors=len(s._mirrors) if s else 0,timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"approval_adapter":self.get_approval_adapter_card().to_dict(),"envelope":self.get_envelope_card().to_dict(),
                "mapping":self.get_mapping_card().to_dict(),"validation":self.get_validation_card().to_dict(),
                "status":self.get_status_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
