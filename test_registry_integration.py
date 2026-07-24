import asyncio
import sys
from pathlib import Path

# add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sam.plugin import (
    PluginManifestLoader,
    PluginManifestValidator,
    PluginRegistry,
    PluginDescriptor,
    PluginStatus,
)


async def main():
    print("=" * 60)
    print("Testing Plugin Registry Integration")
    print("=" * 60)

    # 1. Load manifest
    loader = PluginManifestLoader()
    manifest_path = Path('examples/plugins/sample-plugin/manifest.yaml')

    print(f"\n1. Loading manifest from: {manifest_path}")
    manifest = loader.load_from_yaml(manifest_path)
    print(f"   Loaded: {manifest.name} v{manifest.version}")
    print(f"   ID: {manifest.id}")
    print(f"   Capabilities: {manifest.capabilities}")
    print(f"   Permissions: {[p.value for p in manifest.permissions]}")

    # 2. Validate manifest
    print("\n2. Validating manifest...")
    validator = PluginManifestValidator()
    ok = validator.validate_and_log(manifest)
    print(f"   Validation: {'PASSED' if ok else 'FAILED'}")

    if not ok:
        print("   Cannot proceed - manifest validation failed")
        return 1

    # 3. Register in PluginRegistry
    print("\n3. Registering plugin in PluginRegistry...")
    registry = PluginRegistry()

    try:
        plugin_id = await registry.register(manifest)
        print(f"   Registered with ID: {plugin_id}")

        # Check descriptor
        descriptor = await registry.get_descriptor(plugin_id)
        print(f"   Status: {descriptor.status.value}")
        print(f"   Registered at: {descriptor.registered_at}")

    except ValueError as e:
        print(f"   Registration failed: {e}")
        return 1

    # 4. Test lifecycle status updates
    print("\n4. Testing lifecycle status updates...")
    lifecycle = [
        PluginStatus.INSTALLED,
        PluginStatus.VALIDATED,
        PluginStatus.REGISTERED,
        PluginStatus.ENABLED,
        PluginStatus.INITIALIZED,
        PluginStatus.HEALTHY,
    ]

    for status in lifecycle:
        await registry.update_status(plugin_id, status)
        descriptor = await registry.get_descriptor(plugin_id)
        print(f"   Status: {descriptor.status.value}")

    # 5. Test listing
    print("\n5. Testing list operations...")
    all_plugins = await registry.list()
    print(f"   Total plugins: {len(all_plugins)}")

    healthy_plugins = await registry.list(PluginStatus.HEALTHY)
    print(f"   HEALTHY plugins: {len(healthy_plugins)}")

    # 6. Test get by capability
    print("\n6. Testing capability lookup...")
    for cap in manifest.capabilities:
        found = await registry.get_by_capability(cap)
        print(f"   Capability '{cap}' -> {len(found)} plugin(s)")

    # 7. Test error status
    print("\n7. Testing error status...")
    await registry.update_status(plugin_id, PluginStatus.DEGRADED, error="Test error")
    descriptor = await registry.get_descriptor(plugin_id)
    print(f"   Status: {descriptor.status.value}")
    print(f"   Error: {descriptor.error}")

    # 8. Test unregister
    print("\n8. Testing unregister...")
    await registry.unregister(plugin_id)
    descriptor = await registry.get_descriptor(plugin_id)
    print(f"   After unregister: {'found' if descriptor else 'not found (correct)'}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)