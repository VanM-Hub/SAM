"""
Approval Gateway.

Single official path to Approval Runtime.
Does NOT submit. Preview only.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .submission_plan import ApprovalSubmissionPlan
from .gateway_request import ApprovalGatewayRequest, GatewayReference, GatewayMetadata
from .gateway_router import GatewayRouter
from .gateway_validator import GatewayValidator
from .gateway_registry import GatewayRegistry


@dataclass(frozen=True)
class ApprovalGatewayResult:
    success: bool = False; request_id: str = ""
    route: str = ""; validation_result: Optional[Dict[str,Any]] = None
    warnings: list = field(default_factory=list); errors: list = field(default_factory=list)
    message: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"success":self.success,"request_id":self.request_id,"route":self.route,
        "validation_result":self.validation_result,"warnings":list(self.warnings),"errors":list(self.errors),"message":self.message}


class ApprovalGateway:
    """Single official gateway to Approval Runtime."""

    def __init__(self) -> None:
        self._router = GatewayRouter()
        self._validator = GatewayValidator()
        self._registry = GatewayRegistry()
        self._last_result: Optional[ApprovalGatewayResult] = None
        self._gateway_count: int = 0

    @property
    def router(self): return self._router
    @property
    def validator(self): return self._validator
    @property
    def registry(self): return self._registry
    @property
    def last_result(self): return self._last_result
    @property
    def gateway_count(self): return self._gateway_count

    def process(self, plan: ApprovalSubmissionPlan) -> ApprovalGatewayResult:
        """Process a submission plan through the gateway."""
        # Validate
        validation = self._validator.validate(plan)
        if not validation.get("valid", False):
            result = ApprovalGatewayResult(success=False, validation_result=validation,
                                           errors=validation.get("errors", []), message="Gateway validation failed")
            self._last_result = result; self._gateway_count += 1
            return result

        # Route
        route = self._router.route(plan)
        self._registry.record_route(route)

        # Build gateway request
        gateway_req = ApprovalGatewayRequest(
            request_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            references=GatewayReference(submission_plan_id=plan.plan_id, envelope_id=plan.envelope_id),
            metadata=GatewayMetadata(gateway_id=str(uuid.uuid4()), timestamp=datetime.now().timestamp()),
            payload={"plan_summary": plan.summary, "envelope_id": plan.envelope_id},
            route=route,
            ready=plan.ready,
        )
        self._registry.register(gateway_req)

        result = ApprovalGatewayResult(
            success=True, request_id=gateway_req.request_id,
            route=route, validation_result=validation,
            message=f"Gateway processed — route: {route}",
        )
        self._last_result = result; self._gateway_count += 1
        return result

import uuid
