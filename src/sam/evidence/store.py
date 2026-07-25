"""Evidence Store for SAM with optional SQLite persistence."""

import structlog
from typing import List, Optional, Any
from sam.evidence.models import Evidence, EvidenceType
from sam.events import EventBus, Event

logger = structlog.get_logger()


class EvidenceStore:
    """Evidence store with optional persistence.

    In-memory by default; if a repository is provided, also persists to SQLite.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        repo: Optional[Any] = None
    ) -> None:
        self._evidence: List[Evidence] = []
        self._event_bus: Optional[EventBus] = event_bus
        self._repo: Optional[Any] = repo
        logger.debug("EvidenceStore initialized", initial_count=0, has_persistence=repo is not None)

    async def publish(self, evidence: Evidence) -> None:
        """Publish an evidence record to the store."""
        self._evidence.append(evidence)
        logger.info(
            "Evidence published",
            evidence_id=evidence.id,
            capability_id=evidence.capability_id,
            type=evidence.type.value,
            status=evidence.status.value,
            confidence=evidence.confidence,
        )

        # Persist if repository provided
        if self._repo is not None:
            try:
                correlation_id = None
                if self._evidence and self._evidence[-1] is evidence:
                    # Get correlation from the execution context if available
                    pass
                # Try to get from evidence metadata
                if hasattr(evidence, 'metadata') and isinstance(evidence.metadata, dict):
                    correlation_id = evidence.metadata.get('correlation_id')
                await self._repo.add(evidence, correlation_id=correlation_id)
            except Exception:
                logger.exception("Failed to persist evidence", evidence_id=evidence.id)

        # Publish EvidenceGenerated event to audit trail
        if self._event_bus:
            await self._event_bus.publish(Event(
                type="EvidenceGenerated",
                source="evidence_store",
                payload={
                    "evidence_id": evidence.id,
                    "capability_id": evidence.capability_id,
                    "execution_id": evidence.execution_id,
                    "type": evidence.type.value,
                    "confidence": evidence.confidence,
                    "payload": evidence.payload
                }
            ))

    async def get(self, evidence_id: str) -> Optional[Evidence]:
        """Retrieve a single evidence record by ID."""
        for ev in self._evidence:
            if ev.id == evidence_id:
                logger.debug("Evidence retrieved", evidence_id=evidence_id)
                return ev
        logger.debug("Evidence not found", evidence_id=evidence_id)
        return None

    async def query(
        self,
        capability_id: Optional[str] = None,
        type: Optional[EvidenceType] = None,
        limit: int = 100
    ) -> List[Evidence]:
        """Query evidence records with optional filters."""
        results = self._evidence

        if capability_id:
            results = [e for e in results if e.capability_id == capability_id]

        if type:
            results = [e for e in results if e.type == type]

        # Most recent first
        results = sorted(results, key=lambda e: e.timestamp, reverse=True)

        logger.debug(
            "Evidence query",
            capability_id=capability_id,
            type=type.value if type else None,
            limit=limit,
            matched=len(results),
        )

        return results[:limit]

    async def clear(self) -> None:
        """Clear all evidence records. Primarily for testing."""
        count = len(self._evidence)
        self._evidence.clear()
        logger.info("EvidenceStore cleared", removed=count)

    def __len__(self) -> int:
        return len(self._evidence)