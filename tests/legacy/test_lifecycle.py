import asyncio
import sys
from pathlib import Path

# add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sam.plugin import (
    PluginLifecycleManager,
    PluginRegistry,
    PluginManifest,
    PluginStatus,
)


async def run_lifecycle_test():
    registry = PluginRegistry()
    manager = PluginLifecycleManager(registry)

    # 1. Install (from manifest path)
    plugin_path = Path('examples/plugins/sample-plugin/manifest.yaml')
    plugin_id = await manager.install(plugin_path)
    print('Installed:', plugin_id)

    # 2. Validate
    ok = await manager.validate(plugin_id)
    print('Validated:', ok)

    # 3. Resolve
    resolved = await manager.resolve_dependencies(plugin_id)
    print('Resolved:', resolved)

    # 4. Register (idempotent)
    await manager.register(plugin_id)
    desc = await registry.get_descriptor(plugin_id)
    print('Status after register:', desc.status.value)

    # 5. Enable
    await manager.enable(plugin_id)
    desc = await registry.get_descriptor(plugin_id)
    print('Status after enable:', desc.status.value)

    # 6. Initialize
    class DummyContext: pass
    await manager.initialize(plugin_id, DummyContext())
    desc = await registry.get_descriptor(plugin_id)
    print('Status after initialize:', desc.status.value)

    # 7. Health
    await manager.health_check(plugin_id)
    desc = await registry.get_descriptor(plugin_id)
    print('Status after health:', desc.status.value)

    # 8. Disable
    await manager.disable(plugin_id)
    desc = await registry.get_descriptor(plugin_id)
    print('Status after disable:', desc.status.value)

    # 9. Unload
    await manager.unload(plugin_id)
    desc = await registry.get_descriptor(plugin_id)
    print('Status after unload:', desc.status.value)

    # 10. Uninstall
    await manager.uninstall(plugin_id)
    desc = await registry.get_descriptor(plugin_id)
    print('Status after uninstall:', 'not found' if not desc else desc.status.value)


if __name__ == '__main__':
    asyncio.run(run_lifecycle_test())
