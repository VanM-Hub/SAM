"""
Session Builder.

Builds ApprovalSession from ApprovalGatewayRequest.
Does NOT execute approval. Preview only.
"""

import uuid
from datetime import datetime
from .approval_session import ApprovalSession, ApprovalSessionState, ApprovalSessionReference, ApprovalSessionMetadata
from .gateway_request import ApprovalGatewayRequest


class SessionBuilder:
    def build(self, gateway_request: ApprovalGatewayRequest) -> ApprovalSession:
        refs=None
        if gateway_request.references:
            refs=ApprovalSessionReference(gateway_request_id=gateway_request.request_id,
                submission_plan_id=gateway_request.references.submission_plan_id,
                envelope_id=gateway_request.references.envelope_id)
        return ApprovalSession(
            session_id=str(uuid.uuid4()), timestamp=datetime.now().timestamp(),
            state=ApprovalSessionState.CREATED,
            references=refs,
            metadata=ApprovalSessionMetadata(session_id=str(uuid.uuid4()),created_at=datetime.now().timestamp()),
            payload=gateway_request.payload,
            ready=gateway_request.ready,
        )
