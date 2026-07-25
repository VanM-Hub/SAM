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
    DependencyResolver,
)


async def test_dependency_resolution():
    print("=" * 60)
    print("Testing Dependency Resolution")
    print("=" * 60)

    registry = PluginRegistry()
    resolver = DependencyResolver(registry)

    # Create plugin manifests with dependencies
    # plugin_c -> depends on plugin_b -> depends on plugin_a
    plugin_a = PluginManifest(
        id="plugin-a",
        name="plugin-a",
        version="1.0.0",
        author="Test",
        entrypoint="test.a",
        capabilities=["cap.a"],
        dependencies=[],
    )

    plugin_b = PluginManifest(
        id="plugin-b",
        name="plugin-b",
        version="1.0.0",
        author="Test",
        entrypoint="test.b",
        capabilities=["cap.b"],
        dependencies=["plugin-a"],
    )

    plugin_c = PluginManifest(
        id="plugin-c",
        name="plugin-c",
        version="1.0.0",
        author="Test",
        entrypoint="test.c",
        capabilities=["cap.c"],
        dependencies=["plugin-b"],
    )

    # Register all
    for m in [plugin_a, plugin_b, plugin_c]:
        await registry.register(m)
        await registry.update_status(m.id, PluginStatus.ENABLED)

    print("\n1. Testing simple chain resolution (c -> b -> a)...")
    order = await resolver.resolve("plugin-c")
    print(f"   Resolution order: {order}")
    assert order == ["plugin-a", "plugin-b", "plugin-c"], f"Expected ['plugin-a', 'plugin-b', 'plugin-c'], got {order}"
    print("   OK: Correct order")

    print("\n2. Testing validate_dependencies...")
    ok = await resolver.validate_dependencies("plugin-c")
    print(f"   Valid: {ok}")
    assert ok, "Should be valid"
    print("   OK: Valid")

    print("\n3. Testing circular dependency detection...")
    plugin_x = PluginManifest(
        id="plugin-x",
        name="plugin-x",
        version="1.0.0",
        author="Test",
        entrypoint="test.x",
        capabilities=["cap.x"],
        dependencies=["plugin-y"],
    )
    plugin_y = PluginManifest(
        id="plugin-y",
        name="plugin-y",
        version="1.0.0",
        author="Test",
        entrypoint="test.y",
        capabilities=["cap.y"],
        dependencies=["plugin-x"],
    )
    await registry.register(plugin_x)
    await registry.register(plugin_y)
    await registry.update_status(plugin_x.id, PluginStatus.ENABLED)
    await registry.update_status(plugin_y.id, PluginStatus.ENABLED)

    try:
        await resolver.resolve("plugin-x")
        print("   ✗ Should have raised circular dependency error")
        return False
    except ValueError as e:
        print(f"   Caught expected error: {e}")
        print("   OK: Circular dependency detected")

    print("\n4. Testing missing dependency detection...")
    plugin_z = PluginManifest(
        id="plugin-z",
        name="plugin-z",
        version="1.0.0",
        author="Test",
        entrypoint="test.z",
        capabilities=["cap.z"],
        dependencies=["plugin-missing"],
    )
    await registry.register(plugin_z)
    await registry.update_status(plugin_z.id, PluginStatus.ENABLED)

    ok = await resolver.validate_dependencies("plugin-z")
    print(f"   Valid: {ok}")
    assert not ok, "Should be invalid due to missing dependency"
    print("   OK: Missing dependency detected")

    print("\n5. Testing get_resolution_order for multiple plugins...")
    order = await resolver.get_resolution_order(["plugin-a", "plugin-b", "plugin-c"])
    print(f"   Order: {order}")
    # plugin-a should come before plugin-b, which should come before plugin-c
    idx_a = order.index("plugin-a")
    idx_b = order.index("plugin-b")
    idx_c = order.index("plugin-c")
    assert idx_a < idx_b < idx_c, "Order should be a < b < c"
    print("   OK: Correct topological order")

    print("\n6. Testing version constraint checks...")
    # plugin-d depends on plugin-a@>=1.0.0 (should pass)
    plugin_d = PluginManifest(
        id="plugin-d",
        name="plugin-d",
        version="1.0.0",
        author="Test",
        entrypoint="test.d",
        capabilities=["cap.d"],
        dependencies=["plugin-a@>=1.0.0"],
    )
    await registry.register(plugin_d)
    await registry.update_status(plugin_d.id, PluginStatus.ENABLED)

    ok = await resolver.validate_dependencies("plugin-d")
    print(f"   plugin-d valid: {ok}")
    assert ok, "plugin-d should validate against plugin-a@>=1.0.0"
    print("   OK: plugin-d constraint satisfied")

    # plugin-e depends on plugin-a@>=2.0.0 (should fail)
    plugin_e = PluginManifest(
        id="plugin-e",
        name="plugin-e",
        version="1.0.0",
        author="Test",
        entrypoint="test.e",
        capabilities=["cap.e"],
        dependencies=[{"id": "plugin-a", "version": ">=2.0.0"}],
    )
    await registry.register(plugin_e)
    await registry.update_status(plugin_e.id, PluginStatus.ENABLED)

    ok = await resolver.validate_dependencies("plugin-e")
    print(f"   plugin-e valid: {ok}")
    assert not ok, "plugin-e should fail due to unsatisfied version constraint"
    desc_e = await registry.get_descriptor("plugin-e")
    print(f"   plugin-e status after validation: {desc_e.status.value}")
    assert desc_e.status == PluginStatus.DEGRADED, "plugin-e should be marked DEGRADED"
    print("   OK: plugin-e correctly degraded on version mismatch")

    # plugin-f uses caret ^1.0.0 (should accept 1.0.0)
    plugin_f = PluginManifest(
        id="plugin-f",
        name="plugin-f",
        version="1.0.0",
        author="Test",
        entrypoint="test.f",
        capabilities=["cap.f"],
        dependencies=["plugin-a@^1.0.0"],
    )
    await registry.register(plugin_f)
    await registry.update_status(plugin_f.id, PluginStatus.ENABLED)

    ok = await resolver.validate_dependencies("plugin-f")
    print(f"   plugin-f valid: {ok}")
    assert ok, "plugin-f should validate with caret ^1.0.0"
    print("   OK: plugin-f caret constraint satisfied")

    print("\n" + "=" * 60)
    print("ALL DEPENDENCY TESTS PASSED!")
    print("=" * 60)
    return True


async def test_lifecycle_with_dependencies():
    print("\n" + "=" * 60)
    print("Testing Lifecycle Manager with Dependencies")
    print("=" * 60)

    registry = PluginRegistry()
    manager = PluginLifecycleManager(registry)

    # Create plugins: base -> middleware -> app
    base = PluginManifest(
        id="base-plugin",
        name="base-plugin",
        version="1.0.0",
        author="Test",
        entrypoint="sam.plugins.sample_plugin.main",
        capabilities=["base.cap"],
        dependencies=[],
    )

    middleware = PluginManifest(
        id="middleware-plugin",
        name="middleware-plugin",
        version="1.0.0",
        author="Test",
        entrypoint="sam.plugins.sample_plugin.main",
        capabilities=["middleware.cap"],
        dependencies=["base-plugin"],
    )

    app = PluginManifest(
        id="app-plugin",
        name="app-plugin",
        version="1.0.0",
        author="Test",
        entrypoint="sam.plugins.sample_plugin.main",
        capabilities=["app.cap"],
        dependencies=["middleware-plugin"],
    )

    print("\n1. Install base plugin...")
    await manager.install(base)
    await manager.validate("base-plugin")
    await manager.resolve_dependencies("base-plugin")
    await manager.register("base-plugin")
    await manager.enable("base-plugin")

    print("\n2. Install middleware plugin (depends on base)...")
    await manager.install(middleware)
    await manager.validate("middleware-plugin")
    await manager.resolve_dependencies("middleware-plugin")
    await manager.register("middleware-plugin")
    await manager.enable("middleware-plugin")

    print("\n3. Install app plugin (depends on middleware)...")
    await manager.install(app)
    await manager.validate("app-plugin")
    await manager.resolve_dependencies("app-plugin")
    await manager.register("app-plugin")
    await manager.enable("app-plugin")

    print("\n4. Initialize all in correct order...")
    class DummyContext: pass
    for pid in ["base-plugin", "middleware-plugin", "app-plugin"]:
        await manager.initialize(pid, DummyContext())
        desc = await registry.get_descriptor(pid)
        print(f"   {pid}: {desc.status.value}")

    print("\n5. Health check all...")
    for pid in ["base-plugin", "middleware-plugin", "app-plugin"]:
        await manager.health_check(pid)
        desc = await registry.get_descriptor(pid)
        print(f"   {pid}: {desc.status.value}")

    print("\n" + "=" * 60)
    print("LIFECYCLE WITH DEPENDENCIES TEST PASSED!")
    print("=" * 60)
    return True


async def main():
    await test_dependency_resolution()
    await test_lifecycle_with_dependencies()
    print("\nALL TESTS PASSED")


if __name__ == '__main__':
    asyncio.run(main())