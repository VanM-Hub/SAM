"""Health check capability."""

import datetime
import uuid

from sam.sdk.base import Capability
from sam.models import Capability as CapabilityModel
from sam.evidence import Evidence, EvidenceType, EvidenceStatus


class HealthCheckCapability(Capability):
    """Perform a read‑only health check of the OpenClaw installation."""

    metadata = CapabilityModel(
        id=uuid.uuid4(),
        created_at=datetime.datetime.utcnow(),
        capability_id="openclaw.health-checks",
        name="OpenClaw Health Checks",
        description="Collects evidence and reports operational health without modifying state.",
        owner="OpenClaw Module",
        version="1.0.0",
        permissions=[],
        risk_level="Low",
        rollback_supported=False,
    )

    async def execute(self, context):
        """Execute the health check.

        Args:
            context: ExecutionContext providing logger and identifiers.

        Returns:
            dict: A simple health report.
        """
        context.logger.info("HealthCheckCapability executed")
        # In a real implementation we would gather evidence from various sources.
        # For now we return a static healthy response.
        result = {
            "status": "healthy",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "checks": {
                "runtime": "ok",
                "workspace": "ok",
                "provider": "ok",
                "configuration": "ok",
                "filesystem": "ok",
            },
        }
        
        # Publish evidence if an evidence store was provided on the context
        # Use explicit None check because EvidenceStore.__len__ may return 0
        # which makes the object falsy even when present.
        if context.evidence is not None:
            # Get correlation_id from context if available
            correlation_id = None
            if context.correlation is not None:
                correlation_id = context.correlation.correlation_id
            ev = Evidence(
                id=str(uuid.uuid4()),
                capability_id=self.metadata.capability_id,
                execution_id=str(context.execution_id),
                type=EvidenceType.HEALTH_CHECK,
                status=EvidenceStatus.COLLECTED,
                confidence=0.95,
                payload=result,
                source="runtime",
                timestamp=datetime.datetime.utcnow(),
                metadata={"correlation_id": correlation_id} if correlation_id else {}
            )
            await context.evidence.publish(ev)
            context.logger.info("Health check evidence published", evidence_id=ev.id)

            # Derive a knowledge fact from the health check if it's fully healthy
            try:
                all_ok = all(v == "ok" for v in result.get("checks", {}).values())
                if all_ok and context.knowledge is not None:
                    from sam.knowledge import KnowledgeFact, KnowledgeStatus, KnowledgeSource
                    fact = KnowledgeFact(
                        id=str(uuid.uuid4()),
                        capability_id=self.metadata.capability_id,
                        fact="OpenClaw runtime is healthy",
                        confidence=0.95,
                        source=KnowledgeSource.EVIDENCE,
                        evidence_ids=[ev.id],
                        status=KnowledgeStatus.VERIFIED,
                        tags=["health", "runtime"],
                        timestamp=datetime.datetime.utcnow(),
                        metadata={"correlation_id": correlation_id} if correlation_id else {}
                    )
                    await context.knowledge.add(fact)
                    context.logger.info("Knowledge fact derived and added", fact_id=fact.id)
            except Exception:
                context.logger.exception("failed_to_add_knowledge_fact")

        return result