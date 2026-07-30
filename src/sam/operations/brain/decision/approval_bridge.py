"""
Approval Bridge — One-way adapter from Decision Runtime to Approval Runtime.

Decision Runtime → Approval Adapter → Approval Runtime Interface
No callback. No approval logic. Preview only.
"""

from typing import Dict, Any, Optional
from .approval_envelope import ApprovalRequestEnvelope
from .approval_mapper import ApprovalMapper
from .approval_adapter import ApprovalAdapter, ApprovalAdapterResult
from .approval_preparation import ApprovalPreparation


class ApprovalBridge:
    """One-way bridge from Decision Runtime to Approval Runtime."""

    def __init__(self) -> None:
        self._mapper = ApprovalMapper()
        self._adapter = ApprovalAdapter()
        self._last_envelope: Optional[ApprovalRequestEnvelope] = None
        self._last_result: Optional[ApprovalAdapterResult] = None
        self._bridge_count: int = 0

    @property
    def last_envelope(self) -> Optional[ApprovalRequestEnvelope]:
        return self._last_envelope

    @property
    def last_result(self) -> Optional[ApprovalAdapterResult]:
        return self._last_result

    @property
    def bridge_count(self) -> int:
        return self._bridge_count

    def bridge(self, prep: ApprovalPreparation) -> Dict[str, Any]:
        """Bridge preparation to approval runtime interface."""
        # Map preparation → envelope
        envelope = self._mapper.map(prep)
        self._last_envelope = envelope

        # Process through adapter
        result = self._adapter.process(envelope)
        self._last_result = result
        self._bridge_count += 1

        return {
            "envelope_id": envelope.envelope_id,
            "mapped": True,
            "ready": envelope.ready,
            "adapter_success": result.success,
            "validation_score": result.validation_result.get("score", 0) if result.validation_result else 0,
            "bridge_count": self._bridge_count,
            "note": "Preview only — no approval submitted",
        }
