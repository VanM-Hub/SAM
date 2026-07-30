"""
Submission Builder.

Builds ApprovalSubmissionPlan from ApprovalRequestEnvelope.
Does NOT submit. Preview only.
"""

import uuid
from datetime import datetime
from .approval_envelope import ApprovalRequestEnvelope
from .submission_plan import ApprovalSubmissionPlan, SubmissionMetadata, SubmissionReference, SubmissionStage


class SubmissionBuilder:
    def build(self, envelope: ApprovalRequestEnvelope) -> ApprovalSubmissionPlan:
        stages = []
        stages.append(SubmissionStage(name="validate_envelope", status="completed"))
        stages.append(SubmissionStage(name="check_readiness", status="completed", 
                     result={"ready": envelope.ready}))
        stages.append(SubmissionStage(name="prepare_submission", status="pending",
                     result={"note": "Ready for Approval Runtime — preview only"}))

        return ApprovalSubmissionPlan(
            plan_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            envelope_id=envelope.envelope_id,
            metadata=SubmissionMetadata(submission_id=str(uuid.uuid4()), created_at=datetime.now().timestamp()),
            references=SubmissionReference(envelope_id=envelope.envelope_id) if envelope.references else None,
            stages=stages,
            ready=envelope.ready,
            summary=f"Submission plan {envelope.envelope_id[:8]} — {'ready' if envelope.ready else 'not ready'}",
        )
