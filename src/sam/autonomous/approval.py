"""
Approval Manager — Phase 1

Mengelola permintaan approval untuk tindakan autonomous.
Human-in-the-loop untuk tindakan berisiko tinggi.
"""

import structlog
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from .models import ApprovalRequest

logger = structlog.get_logger()


class ApprovalManager:
    """Manager approval — pending queue, approve, deny, expired cleanup."""

    EXPIRY_MINUTES = 30

    def __init__(self):
        self._requests: Dict[str, ApprovalRequest] = {}
        self._history: List[ApprovalRequest] = []

    async def request(
        self,
        action_id: str,
        requester: str = "autonomous",
        reason: str = "Autonomous action requires human review",
    ) -> ApprovalRequest:
        """Buat permintaan approval untuk suatu tindakan.

        Args:
            action_id: ID tindakan yang butuh approval.
            requester: Sumber request (autonomous, operator).
            reason: Alasan kenapa perlu approval.

        Returns:
            ApprovalRequest yang baru dibuat.
        """
        request = ApprovalRequest(
            action_id=action_id,
            requester=requester,
            reason=reason,
            expires_at=datetime.utcnow() + timedelta(minutes=self.EXPIRY_MINUTES),
        )
        self._requests[request.id] = request
        logger.info(
            "approval_requested",
            request_id=request.id,
            action_id=action_id,
            expires_at=request.expires_at.isoformat(),
        )
        return request

    async def approve(self, request_id: str) -> bool:
        """Setujui permintaan approval.

        Returns:
            True jika berhasil.
        """
        request = self._requests.get(request_id)
        if not request:
            logger.warning("approval_request_not_found", request_id=request_id)
            return False

        if request.status != "pending":
            logger.warning("approval_already_processed", request_id=request_id, status=request.status)
            return False

        request.status = "approved"

        # Archive to history
        self._history.append(request)
        del self._requests[request_id]

        logger.info("approval_granted", request_id=request_id, action_id=request.action_id)
        return True

    async def deny(self, request_id: str) -> bool:
        """Tolak permintaan approval.

        Returns:
            True jika berhasil.
        """
        request = self._requests.get(request_id)
        if not request:
            logger.warning("approval_request_not_found", request_id=request_id)
            return False

        if request.status != "pending":
            logger.warning("approval_already_processed", request_id=request_id, status=request.status)
            return False

        request.status = "denied"

        self._history.append(request)
        del self._requests[request_id]

        logger.info("approval_denied", request_id=request_id, action_id=request.action_id)
        return True

    def get_pending(self) -> List[ApprovalRequest]:
        """Ambil semua request yang masih pending dan belum expired."""
        now = datetime.utcnow()
        pending = []
        expired_ids = []

        for req_id, req in self._requests.items():
            if req.expires_at and req.expires_at < now:
                expired_ids.append(req_id)
                continue
            if req.status == "pending":
                pending.append(req)

        # Clean up expired
        for req_id in expired_ids:
            req = self._requests.pop(req_id)
            self._history.append(req)
            logger.info("approval_expired", request_id=req_id)

        return pending

    def get_history(self, limit: int = 50) -> List[ApprovalRequest]:
        """Ambil history approval."""
        return self._history[-limit:] if limit else self._history
