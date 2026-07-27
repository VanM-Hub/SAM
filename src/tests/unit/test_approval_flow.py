#!/usr/bin/env python
"""Combined test: run capability + approve in same process to verify approval flow."""
import asyncio
import uuid
from sam.runtime.registry import CapabilityRegistry
from sam.runtime.factory import CapabilityFactory
from sam.runtime.runtime import CapabilityRuntime
from sam.runtime.context import ExecutionContext
from sam.runtime.discovery import CapabilityDiscovery
from sam.knowledge.loader import KnowledgeLoader
from sam.events import EventBus, Event
from sam.services import AuditService
from sam.evidence.store import EvidenceStore
from sam.knowledge.store import KnowledgeStore
from sam.patterns.engine import PatternEngine
from sam.patterns.models import PatternRule, PatternSeverity
from sam.recommendations.engine import RecommendationEngine
from sam.recommendations.models import RecommendationSeverity
from sam.approval.engine import ApprovalEngine
from sam.approval.models import ApprovalDecision

import os
SAM_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")


async def main():
    event_bus = EventBus()
    AuditService(event_bus)

    # Build runtime
    loader = KnowledgeLoader(SAM_ROOT)
    loader.load_all()
    registry = CapabilityRegistry()
    discovery = CapabilityDiscovery(registry, loader)
    await discovery.discover()
    factory = CapabilityFactory()
    evidence_store = EvidenceStore(event_bus=event_bus)
    knowledge_store = KnowledgeStore()
    pattern_engine = PatternEngine()

    # Register default pattern rule
    healthy_rule = PatternRule(
        id="health-ok",
        name="All health checks passed",
        condition="All health checks are ok",
        severity=PatternSeverity.INFO,
        tags=["health"],
        min_confidence=0.9,
        enabled=True
    )
    await pattern_engine.register_rule(healthy_rule)

    # Recommendation engine with HIGH severity template
    recommendation_engine = RecommendationEngine(event_bus)
    await recommendation_engine.register_rule_action(
        rule_id="health-ok",
        template={
            "severity": RecommendationSeverity.HIGH,
            "title": "System health check passed",
            "description": "All health checks completed successfully.",
            "action_hint": "No action required",
        },
    )

    # Approval engine
    approval_engine = ApprovalEngine(event_bus)

    runtime = CapabilityRuntime(registry, factory)

    # Run capability
    execution_id = str(uuid.uuid4())
    context = ExecutionContext(
        execution_id=uuid.UUID(execution_id),
        workflow_id="",
        step_name="standalone",
        inputs={},
        evidence=evidence_store,
        knowledge=knowledge_store,
    )

    await event_bus.publish(Event(
        type="CapabilityStarted",
        source="cli",
        payload={"capability_id": "openclaw.health-checks", "execution_id": execution_id, "inputs": {}}
    ))

    result = await runtime.execute_capability("openclaw.health-checks", context)

    # Evaluate patterns
    new_facts = await knowledge_store.query(capability_id="openclaw.health-checks")
    if new_facts:
        detections = await pattern_engine.evaluate(new_facts)
        for detection in detections:
            await event_bus.publish(Event(
                type="PatternDetected",
                source="pattern_engine",
                payload={
                    "detection_id": detection.id,
                    "rule_id": detection.rule_id,
                    "severity": detection.severity.value,
                    "message": detection.message,
                    "knowledge_fact_ids": detection.knowledge_fact_ids,
                    "execution_id": execution_id,
                    "metadata": detection.metadata
                }
            ))

    # Wait a bit for async event processing
    await asyncio.sleep(0.1)

    # Check pending approvals
    print("\n=== PENDING APPROVALS ===")
    pending = await approval_engine.get_pending()
    if not pending:
        print("No pending approvals")
    else:
        for req in pending:
            print(f" - id={req.id} title={req.title} severity={req.severity} status={req.status.value}")
            # Make a decision (APPROVE)
            print(f"\n=== DECIDING: APPROVE {req.id} ===")
            updated = await approval_engine.decide(req.id, ApprovalDecision.APPROVE, decided_by="human_test")
            if updated:
                print(f"Decision recorded: status={updated.status.value} decision={updated.decision.value}")

    # Show all requests
    print("\n=== ALL APPROVAL REQUESTS ===")
    all_reqs = await approval_engine.get_requests(limit=10)
    for req in all_reqs:
        print(f" - id={req.id} title={req.title} severity={req.severity} status={req.status.value} decision={req.decision.value if req.decision else 'N/A'}")

    print(f"\n=== CAPABILITY RESULT ===")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())