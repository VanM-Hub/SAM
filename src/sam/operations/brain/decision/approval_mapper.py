"""
Approval Mapper.

Maps ApprovalPreparation to ApprovalRequestEnvelope.
Deterministic. No Approval Runtime knowledge.
"""

import uuid
from datetime import datetime

from .approval_preparation import ApprovalPreparation, ApprovalCandidate
from .approval_envelope import ApprovalRequestEnvelope, ApprovalReference, ApprovalPayload


class ApprovalMapper:
    """Maps approval preparation to envelope."""

    def map(self, prep: ApprovalPreparation) -> ApprovalRequestEnvelope:
        """Map preparation to envelope."""
        references = None
        if prep.metadata:
            references = ApprovalReference(
                preparation_id=prep.preparation_id,
                plan_id=prep.metadata.plan_id,
                evaluation_id=prep.metadata.evaluation_id,
            )

        candidates = prep.candidates
        payload = None
        if candidates:
            c = candidates[0]
            payload = ApprovalPayload(
                action_type=c.action_type,
                runtime_ids=[c.runtime_id] if c.runtime_id else [],
                priority=c.priority,
                confidence=c.confidence,
                evidence_summary=prep.summary,
                requires_approval=c.requires_approval,
            )

        return ApprovalRequestEnvelope(
            envelope_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            references=references,
            payload=payload,
            ready=prep.ready_for_submission,
        )
