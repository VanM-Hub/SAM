import asyncio
import os
from sam.runtime.registry import CapabilityRegistry
from sam.runtime.runtime import CapabilityRuntime
from sam.knowledge.loader import KnowledgeLoader
from sam.runtime.discovery import CapabilityDiscovery


async def test():
    loader = KnowledgeLoader(os.getcwd())
    loader.load_all()
    registry = CapabilityRegistry()
    discovery = CapabilityDiscovery(registry=registry, loader=loader)
    await discovery.discover()
    print("Capabilities in registry:", list(registry._capabilities.keys()))
    for cid, cap_class in registry._capabilities.items():
        print(f"  {cid}: {cap_class}")
        if hasattr(cap_class, "metadata"):
            print(f"  metadata: {cap_class.metadata}")
    # Now create a runtime and try to execute
    runtime = CapabilityRuntime(registry)
    print("Executors in runtime:", list(runtime._executors.keys()))


asyncio.run(test())
