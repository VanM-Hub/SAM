"""Manual test runner for Knowledge Store integration verification.

This runner verifies that HealthCheckCapability adds a KnowledgeFact to the
KnowledgeStore when all health checks pass, without requiring pytest.
"""

import asyncio
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sam.runtime.registry import CapabilityRegistry
from sam.runtime.factory import CapabilityFactory
from sam.runtime.runtime import CapabilityRuntime
from sam.runtime.context import ExecutionContext
from sam.knowledge.loader import KnowledgeLoader
from sam.runtime.discovery import CapabilityDiscovery
from sam.events import EventBus
from sam.evidence.store import EvidenceStore
from sam.knowledge.store import KnowledgeStore
from sam.capabilities.health_checks import HealthCheckCapability
import uuid


async def test_knowledge_fact_added():
    """Test that HealthCheckCapability adds KnowledgeFact to KnowledgeStore."""
    print("Building runtime pipeline...")

    # Setup loader and registry
    loader = KnowledgeLoader("D:/Project AI/SAM")
    loader.load_all()

    registry = CapabilityRegistry()
    discovery = CapabilityDiscovery(registry, loader)
    await discovery.discover()

    factory = CapabilityFactory()
    evidence_store = EvidenceStore()
    knowledge_store = KnowledgeStore()

    runtime = CapabilityRuntime(registry, factory)

    # Execute health check capability
    execution_id = uuid.uuid4()
    context = ExecutionContext(
        execution_id=execution_id,
        workflow_id="test",
        step_name="health_check",
        inputs={},
        evidence=evidence_store,
        knowledge=knowledge_store,
    )

    print("Executing HealthCheckCapability...")
    result = await runtime.execute_capability("openclaw.health-checks", context)

    print(f"Capability result: {result}")

    # Verify evidence was published
    evidence_list = await evidence_store.query(capability_id="openclaw.health-checks")
    print(f"Evidence count: {len(evidence_list)}")

    if not evidence_list:
        print("FAIL: No evidence published")
        return False

    evidence = evidence_list[0]
    print(f"Evidence ID: {evidence.id}")
    print(f"Evidence type: {evidence.type}")
    print(f"Evidence confidence: {evidence.confidence}")

    # Verify knowledge fact was added
    facts = await knowledge_store.query(capability_id="openclaw.health-checks")
    print(f"Knowledge fact count: {len(facts)}")

    if not facts:
        print("FAIL: No knowledge fact added to KnowledgeStore")
        return False

    fact = facts[0]
    print(f"Fact ID: {fact.id}")
    print(f"Fact: {fact.fact}")
    print(f"Fact confidence: {fact.confidence}")
    print(f"Fact source: {fact.source}")
    print(f"Fact status: {fact.status}")
    print(f"Fact tags: {fact.tags}")
    print(f"Fact evidence_ids: {fact.evidence_ids}")

    # Verify the fact references the evidence
    if evidence.id not in fact.evidence_ids:
        print("FAIL: Knowledge fact does not reference the evidence ID")
        return False

    # Verify fact content
    expected_fact = "OpenClaw runtime is healthy"
    if fact.fact != expected_fact:
        print(f"FAIL: Fact text mismatch. Expected: '{expected_fact}', Got: '{fact.fact}'")
        return False

    if fact.source.value != "evidence":
        print(f"FAIL: Fact source should be 'evidence', got: {fact.source}")
        return False

    if fact.status.value != "verified":
        print(f"FAIL: Fact status should be 'verified', got: {fact.status}")
        return False

    if fact.confidence != 0.95:
        print(f"FAIL: Fact confidence should be 0.95, got: {fact.confidence}")
        return False

    print("\nPASS: HealthCheckCapability correctly added KnowledgeFact to KnowledgeStore")
    print("      Evidence -> Knowledge flow verified end-to-end")
    return True


async def main():
    print("=" * 60)
    print("Manual Test: Knowledge Store Integration")
    print("=" * 60)

    try:
        success = await test_knowledge_fact_added()
        if success:
            print("\n" + "=" * 60)
            print("ALL TESTS PASSED")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("TESTS FAILED")
            print("=" * 60)
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())