"""Approval Gate engine for SAM Framework.

Listens to RecommendationGenerated events and manages human approval workflow.
"""

import structlog
from typing import List, Dict, Any, Optional
from sam.events import EventBus, Event
from sam.approval.models import ApprovalRequest, ApprovalStatus, ApprovalDecision

logger = structlog.get_logger()

# Severity levels that require human approval
HIGH_SEVERITY_LEVELS = {"high", "critical"}


class ApprovalEngine:
    """Engine that manages approval requests for high-severity recommendations.

    Optionally persists approval requests via a repository implementing add(req).
    """

    def __init__(self, event_bus: EventBus, repo: Optional[Any] = None) -> None:
        self._requests: List[ApprovalRequest] = []
        self._event_bus = event_bus
        self._repo = repo
        self._subscribed = False

        # Subscribe to recommendation events
        self._subscribe()

    def _subscribe(self) -> None:
        """Subscribe to RecommendationGenerated events on the event bus."""
        if not self._subscribed:
            self._event_bus.subscribe("RecommendationGenerated", self._handle_recommendation)
            self._subscribed = True
            logger.info("ApprovalEngine subscribed to RecommendationGenerated events")

    def _requires_approval(self, severity: str) -> bool:
        """Check if a severity level requires human approval."""
        return severity.lower() in HIGH_SEVERITY_LEVELS

    async def _handle_recommendation(self, event: Event) -> None:
        """Handle a RecommendationGenerated event and create approval request if needed."""
        payload = event.payload or {}
        recommendation_id = payload.get("recommendation_id")
        severity = payload.get("severity", "info")
        title = payload.get("title", "")
        description = payload.get("description", "")
        action_hint = payload.get("action_hint", "")
        metadata = payload.get("metadata", {})

        if not recommendation_id:
            logger.warning("RecommendationGenerated event missing recommendation_id")
            return

        requires_approval = self._requires_approval(severity)

        if requires_approval:
            # Create pending approval request
            request = ApprovalRequest(
                recommendation_id=recommendation_id,
                severity=severity,
                title=title,
                description=description,
                action_hint=action_hint,
                status=ApprovalStatus.PENDING,
                metadata=metadata,
            )
            self._requests.append(request)

            # Persist if repository provided
            if self._repo is not None:
                try:
                    correlation_id = metadata.get("correlation_id") if isinstance(metadata, dict) else None
                    await self._repo.add(request, correlation_id=correlation_id)
                except Exception:
                    logger.exception("Failed to persist approval request", approval_request_id=request.id)


            # Publish ApprovalRequired event
            await self._event_bus.publish(Event(
                type="ApprovalRequired",
                source="approval_engine",
                payload={
                    "approval_request_id": request.id,
                    "recommendation_id": recommendation_id,
                    "severity": severity,
                    "title": title,
                    "description": description,
                    "action_hint": action_hint,
                    "status": request.status.value,
                    "timestamp": request.timestamp.isoformat(),
                    "metadata": metadata,
                },
            ))

            logger.info(
                "Approval required",
                approval_request_id=request.id,
                recommendation_id=recommendation_id,
                severity=severity,
            )
        else:
            # Auto-approve for low severity
            request = ApprovalRequest(
                recommendation_id=recommendation_id,
                severity=severity,
                title=title,
                description=description,
                action_hint=action_hint,
                status=ApprovalStatus.APPROVED,
                decision=ApprovalDecision.APPROVE,
                decided_by="auto",
                decided_at=datetime.utcnow(),
                metadata=metadata,
            )
            self._requests.append(request)

            # Persist auto-approved request if repo present
            if self._repo is not None:
                try:
                    correlation_id = metadata.get("correlation_id") if isinstance(metadata, dict) else None
                    await self._repo.add(request, correlation_id=correlation_id)
                except Exception:
                    logger.exception("Failed to persist auto-approved request", approval_request_id=request.id)


            # Publish ApprovalGranted event
            await self._event_bus.publish(Event(
                type="ApprovalGranted",
                source="approval_engine",
                payload={
                    "approval_request_id": request.id,
                    "recommendation_id": recommendation_id,
                    "severity": severity,
                    "title": title,
                    "decision": ApprovalDecision.APPROVE.value,
                    "decided_by": "auto",
                    "decided_at": request.decided_at.isoformat() if request.decided_at else None,
                    "metadata": metadata,
                },
            ))

            logger.info(
                "Auto-approved (low severity)",
                approval_request_id=request.id,
                recommendation_id=recommendation_id,
                severity=severity,
            )

    async def decide(
        self,
        request_id: str,
        decision: ApprovalDecision,
        decided_by: str = "human"
    ) -> Optional[ApprovalRequest]:
        """Make a decision on a pending approval request.

        Args:
            request_id: The approval request ID.
            decision: The decision to make (APPROVE, DENY, DEFER).
            decided_by: Who made the decision (default: "human").

        Returns:
            The updated ApprovalRequest if found, None otherwise.
        """
        for request in self._requests:
            if request.id == request_id:
                if request.status != ApprovalStatus.PENDING:
                    logger.warning(
                        "Cannot decide on non-pending request",
                        request_id=request_id,
                        current_status=request.status.value,
                    )
                    return request

                request.decision = decision
                request.decided_by = decided_by
                request.decided_at = datetime.utcnow()

                if decision == ApprovalDecision.APPROVE:
                    request.status = ApprovalStatus.APPROVED
                    event_type = "ApprovalGranted"
                elif decision == ApprovalDecision.DENY:
                    request.status = ApprovalStatus.DENIED
                    event_type = "ApprovalDenied"
                else:  # DEFER
                    request.status = ApprovalStatus.PENDING  # Keep pending
                    event_type = "ApprovalDeferred"

                # Publish decision event
                await self._event_bus.publish(Event(
                    type=event_type,
                    source="approval_engine",
                    payload={
                        "approval_request_id": request.id,
                        "recommendation_id": request.recommendation_id,
                        "severity": request.severity,
                        "title": request.title,
                        "decision": decision.value,
                        "decided_by": decided_by,
                        "decided_at": request.decided_at.isoformat(),
                        "metadata": request.metadata,
                    },
                ))

                logger.info(
                    "Approval decision made",
                    approval_request_id=request.id,
                    decision=decision.value,
                    decided_by=decided_by,
                    new_status=request.status.value,
                )
                # Persist updated request if repo present
                if self._repo is not None:
                    try:
                        correlation_id = request.metadata.get("correlation_id") if isinstance(request.metadata, dict) else None
                        await self._repo.add(request, correlation_id=correlation_id)
                    except Exception:
                        logger.exception("Failed to persist approval decision", approval_request_id=request.id)
                return request

        logger.warning("Approval request not found", request_id=request_id)
        return None

    async def get_pending(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return [r for r in self._requests if r.status == ApprovalStatus.PENDING]

    async def get_requests(self, limit: int = 100) -> List[ApprovalRequest]:
        """Get all approval requests, most recent first."""
        sorted_requests = sorted(self._requests, key=lambda r: r.timestamp, reverse=True)
        return sorted_requests[:limit]

    async def clear(self) -> None:
        """Clear all requests. Primarily for testing."""
        count = len(self._requests)
        self._requests.clear()
        logger.info("ApprovalEngine cleared", requests=count)


# Need to import datetime
from datetime import datetime