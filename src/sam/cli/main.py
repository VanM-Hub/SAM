import typer
import asyncio
import uuid
import structlog
from pathlib import Path
from typing import Optional, List, Dict, Any

from sam.runtime.registry import CapabilityRegistry
from sam.runtime.runtime import CapabilityRuntime
from sam.runtime.context import ExecutionContext
from sam.runtime.workflow import WorkflowEngine
from sam.knowledge.loader import KnowledgeLoader
from sam.knowledge.importer import KnowledgeImporter
from sam.knowledge.store import create_knowledge_store
from sam.knowledge.graph import create_knowledge_graph
from uuid import UUID
from sam.runtime.discovery import CapabilityDiscovery
from sam.events import EventBus, Event
from sam.services import AuditService
from sam.plugin import (
    PluginManifestLoader,
    create_plugin_registry,
    PluginStatus,
    create_plugin_discovery,
    PluginLifecycleManager,
    PluginManifest,
)
from sam.core.daemon import RuntimeDaemon, DaemonConfig
from sam.core.job_queue import JobQueue
from sam.core.job import Job, JobType
from sam.core.notification_service import NotificationService
from sam.core.scheduler import Scheduler
from sam.models import Capability

app = typer.Typer()
logger = structlog.get_logger()

# Path to SAM repository (default)
SAM_ROOT = "D:/Project AI/SAM"
DB_PATH = "D:/Project AI/SAM/sam.db"


async def _run_capability(
    capability_id: str,
    inputs: Optional[Dict[str, Any]] = None,
    enable_audit: bool = True
) -> Dict[str, Any]:
    """Internal function to run a single capability with audit."""
    execution_id = str(uuid.uuid4())

    # Setup Event Bus & Audit
    event_bus = EventBus()
    audit_service = AuditService(event_bus) if enable_audit else None

    # Load knowledge & discovery
    loader = KnowledgeLoader(SAM_ROOT)
    store = await create_knowledge_store(DB_PATH)
    await loader.load_all(store=store)

    registry = CapabilityRegistry()
    discovery = CapabilityDiscovery(registry, loader)
    await discovery.discover()

    runtime = CapabilityRuntime(registry)
    context = ExecutionContext(
        execution_id=uuid.UUID(execution_id),
        workflow_id="",
        step_name="standalone",
        inputs=inputs or {},
    )

    # Publish CapabilityStarted
    await event_bus.publish(Event(
        type="CapabilityStarted",
        source="cli",
        payload={
            "capability_id": capability_id,
            "execution_id": execution_id,
            "inputs": inputs or {}
        }
    ))

    try:
        result = await runtime.execute_capability(capability_id, context)

        # Publish CapabilityExecuted
        await event_bus.publish(Event(
            type="CapabilityExecuted",
            source="cli",
            payload={
                "capability_id": capability_id,
                "execution_id": execution_id,
                "result": result
            }
        ))
        return {"success": True, "result": result, "execution_id": execution_id}

    except Exception as e:
        # Publish CapabilityFailed
        await event_bus.publish(Event(
            type="CapabilityFailed",
            source="cli",
            payload={
                "capability_id": capability_id,
                "execution_id": execution_id,
                "error": str(e)
            }
        ))
        raise


async def _run_workflow(
    steps: List[str],
    inputs: Optional[Dict[str, Any]] = None,
    enable_audit: bool = True
) -> List[Any]:
    """Internal function to run a workflow with audit."""
    execution_id = str(uuid.uuid4())

    event_bus = EventBus()
    audit_service = AuditService(event_bus) if enable_audit else None

    loader = KnowledgeLoader(SAM_ROOT)
    store = await create_knowledge_store(DB_PATH)
    await loader.load_all(store=store)

    registry = CapabilityRegistry()
    discovery = CapabilityDiscovery(registry, loader)
    await discovery.discover()

    runtime = CapabilityRuntime(registry)
    context = ExecutionContext(
        execution_id=uuid.UUID(execution_id),
        workflow_id="workflow",
        step_name="workflow_start",
        inputs=inputs or {},
    )

    await event_bus.publish(Event(
        type="WorkflowStarted",
        source="cli",
        payload={
            "steps": steps,
            "execution_id": execution_id
        }
    ))

    try:
        engine = WorkflowEngine(runtime)
        results = await engine.run(steps, context)

        await event_bus.publish(Event(
            type="WorkflowCompleted",
            source="cli",
            payload={
                "steps": steps,
                "execution_id": execution_id,
                "results": results
            }
        ))
        return results

    except Exception as e:
        await event_bus.publish(Event(
            type="WorkflowFailed",
            source="cli",
            payload={
                "steps": steps,
                "execution_id": execution_id,
                "error": str(e)
            }
        ))
        raise


@app.command()
def run(
    capability_id: str,
    no_audit: bool = False
):
    """Run a single capability by ID."""
    async def _run():
        try:
            result = await _run_capability(capability_id, enable_audit=not no_audit)
            typer.echo(f"Result: {result['result']}")
            if not no_audit:
                typer.echo(f"Execution ID: {result['execution_id']}")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_run())


@app.command()
def workflow(
    steps: str,
    no_audit: bool = False
):
    """Run a workflow with comma-separated capability IDs."""
    step_list = [s.strip() for s in steps.split(",") if s.strip()]

    async def _run():
        try:
            results = await _run_workflow(step_list, enable_audit=not no_audit)
            typer.echo(f"Workflow results: {results}")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_run())


# Keep existing knowledge and discovery commands unchanged
@app.command()
def knowledge_load(
    root_path: str = typer.Option(
        "D:/Project AI/SAM", help="Root path of the SAM repository"
    ),
):
    """Load all knowledge markdown files from docs/ and modules/ and persist to DB."""
    async def _load():
        loader = KnowledgeLoader(root_path=root_path)
        store = await create_knowledge_store(DB_PATH)
        docs = await loader.load_all(store=store)
        typer.echo(f"Loaded {len(docs)} knowledge documents.")
        for doc in docs[:5]:  # Show first few
            typer.echo(f" - {doc.title} ({doc.path})")
        if len(docs) > 5:
            typer.echo(f"   ... and {len(docs) - 5} more")
        await store.close()
    asyncio.run(_load())


@app.command()
def knowledge_list():
    """List currently loaded knowledge documents from DB."""
    async def _list():
        root_path = "D:/Project AI/SAM"
        loader = KnowledgeLoader(root_path=root_path)
        store = await create_knowledge_store(DB_PATH)
        docs = await loader.load_all(store=store)
        if not docs:
            typer.echo("No knowledge documents loaded.")
            await store.close()
            return
        typer.echo(f"Loaded {len(docs)} knowledge documents:")
        for doc in docs:
            typer.echo(
                f" - {doc.title} | {doc.path} | v{doc.version} | {doc.status}"
            )
        await store.close()
    asyncio.run(_list())


@app.command()
def discover():
    """Discover capabilities from knowledge metadata and register them."""
    async def _discover():
        root_path = "D:/Project AI/SAM"
        loader = KnowledgeLoader(root_path=root_path)
        store = await create_knowledge_store(DB_PATH)
        await loader.load_all(store=store)
        registry = CapabilityRegistry()
        discovery = CapabilityDiscovery(registry=registry, loader=loader)
        registered = await discovery.discover()
        typer.echo(f"Discovered and registered {len(registered)} capability(ies):")
        for cid in registered:
            typer.echo(f" - {cid}")
        await store.close()
    asyncio.run(_discover())


# Knowledge Relationship subcommands
knowledge_app = typer.Typer()
app.add_typer(knowledge_app, name="knowledge")


@knowledge_app.command("rel-add")
def knowledge_rel_add(
    source_id: str = typer.Argument(..., help="Source fact UUID"),
    target_id: str = typer.Argument(..., help="Target fact UUID"),
    rel_type: str = typer.Argument(..., help="Relationship type (e.g., supports, depends_on, related_to)"),
):
    """Add a relationship between two knowledge facts."""
    async def _add():
        graph = await create_knowledge_graph(DB_PATH)
        rel_id = await graph.add_relationship(
            source_id=UUID(source_id),
            target_id=UUID(target_id),
            rel_type=rel_type,
        )
        typer.echo(f"Created relationship {rel_id}")
        await graph.close()
    asyncio.run(_add())


@knowledge_app.command("rel-list")
def knowledge_rel_list(
    source_id: str = typer.Option(None, "--source", help="Filter by source fact UUID"),
    target_id: str = typer.Option(None, "--target", help="Filter by target fact UUID"),
    rel_type: str = typer.Option(None, "--type", help="Filter by relationship type"),
):
    """List knowledge relationships with optional filters."""
    async def _list():
        graph = await create_knowledge_graph(DB_PATH)
        rels = await graph.get_relationships(
            source_id=UUID(source_id) if source_id else None,
            target_id=UUID(target_id) if target_id else None,
            rel_type=rel_type,
        )
        if not rels:
            typer.echo("No relationships found.")
            await graph.close()
            return
        for rel in rels:
            typer.echo(f" - {rel.id} | {rel.relationship_type} | {rel.source_id} -> {rel.target_id}")
        await graph.close()
    asyncio.run(_list())


@knowledge_app.command("rel-delete")
def knowledge_rel_delete(
    rel_id: str = typer.Argument(..., help="Relationship UUID to delete"),
):
    """Delete a knowledge relationship by ID."""
    async def _delete():
        graph = await create_knowledge_graph(DB_PATH)
        await graph.delete_relationship(UUID(rel_id))
        typer.echo(f"Deleted relationship {rel_id}")
        await graph.close()
    asyncio.run(_delete())


@knowledge_app.command("query")
def knowledge_query(
    source_id: Optional[str] = typer.Option(None, "--source", help="Filter by source fact UUID"),
    target_id: Optional[str] = typer.Option(None, "--target", help="Filter by target fact UUID"),
    rel_type: Optional[str] = typer.Option(None, "--type", help="Filter by relationship type"),
    metadata: Optional[str] = typer.Option(None, "--metadata", help="JSON metadata filter, e.g. '{\"key\": \"value\"}'"),
    search: Optional[str] = typer.Option(None, "--search", help="Text search across facts and metadata"),
    limit: int = typer.Option(50, "--limit", help="Limit results"),
    offset: int = typer.Option(0, "--offset", help="Offset results"),
):
    """Query knowledge relationships with filters or text search."""
    async def _query():
        graph = await create_knowledge_graph(DB_PATH)
        try:
            if search:
                results = await graph.search_fts(search, limit=limit)
                if not results:
                    typer.echo("No results for search.")
                    await graph.close()
                    return
                for r in results:
                    typer.echo(f"- {r['knowledge_id']} | rank={r['rank']:.3f} | {r['category']} | {r['statement']}")
                    if r['metadata']:
                        typer.echo(f"   metadata: {r['metadata']}")
                await graph.close()
                return

            metadata_filter = None
            if metadata:
                try:
                    import json as _json
                    metadata_filter = _json.loads(metadata)
                except Exception:
                    typer.echo("Invalid metadata JSON", err=True)
                    await graph.close()
                    raise typer.Exit(1)

            rels = await graph.query(
                source_id=UUID(source_id) if source_id else None,
                target_id=UUID(target_id) if target_id else None,
                rel_type=rel_type,
                metadata_filter=metadata_filter,
                limit=limit,
                offset=offset,
            )

            if not rels:
                typer.echo("No relationships found.")
                await graph.close()
                return

            for rel in rels:
                typer.echo(f" - {rel.id} | {rel.relationship_type} | {rel.source_id} -> {rel.target_id}")
        finally:
            await graph.close()

    asyncio.run(_query())


@knowledge_app.command("import")
def knowledge_import(
    path: str = typer.Argument(..., help="Path to file to import (.md, .yaml, .json)"),
    file_type: Optional[str] = typer.Option(None, "--type", help="File type: yaml|json|md (auto-detected from extension)"),
):
    """Import knowledge facts from a file into the store (supports .md, .yaml, .json)."""
    async def _import():
        p = Path(path)
        if not p.exists():
            typer.echo(f"File not found: {path}", err=True)
            raise typer.Exit(1)

        ftype = file_type or p.suffix.lstrip('.').lower()
        store = await create_knowledge_store(DB_PATH)

        try:
            if ftype in ("yaml", "yml"):
                importer = KnowledgeImporter()
                created = await importer.import_yaml(p, store)
                typer.echo(f"Imported {len(created)} facts from {path}")
            elif ftype == "json":
                importer = KnowledgeImporter()
                created = await importer.import_json(p, store)
                typer.echo(f"Imported {len(created)} facts from {path}")
            elif ftype == "md":
                loader = KnowledgeLoader(p.parent)
                docs = await loader.load_all(store=store)
                typer.echo(f"Loaded {len(docs)} documents from {p.parent}")
            else:
                typer.echo(f"Unsupported file type: {ftype}", err=True)
                raise typer.Exit(1)
        finally:
            await store.close()

    asyncio.run(_import())


@knowledge_app.command("history")
def knowledge_history(
    fact_id: str = typer.Argument(..., help="Fact UUID to show history for")
):
    """Show version history for a knowledge fact."""
    async def _history():
        store = await create_knowledge_store(DB_PATH)
        try:
            from uuid import UUID as _UUID

            h = await store.list_history(_UUID(fact_id))
            if not h:
                typer.echo("No history found for fact")
                await store.close()
                return
            typer.echo(f"History for fact {fact_id}:")
            for entry in h:
                typer.echo(f" - v{entry.version} | {entry.change_type} | by {entry.changed_by} @ {entry.changed_at}")
                typer.echo(f"   snapshot: {entry.payload_snapshot}")
        finally:
            await store.close()

    asyncio.run(_history())


# Plugin management commands
plugin_app = typer.Typer()
app.add_typer(plugin_app, name="plugin")


@plugin_app.command("install")
def plugin_install(
    path: str = typer.Argument(..., help="Path to plugin directory containing manifest.yaml"),
):
    """Install a plugin from a directory."""
    async def _install():
        try:
            loader = PluginManifestLoader()
            manifest = loader.load_from_directory(Path(path))
            if not manifest:
                typer.echo("No manifest found in directory", err=True)
                raise typer.Exit(1)
            
            plugin_registry = await create_plugin_registry(DB_PATH)
            
            for m in manifest:
                plugin_id = await plugin_registry.install_from_manifest(m)
                typer.echo(f"Installed plugin: {m.name} (ID: {plugin_id})")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    
    asyncio.run(_install())


@plugin_app.command("list")
def plugin_list(
    status: Optional[str] = typer.Option(None, help="Filter by status (INSTALLED, VALIDATED, REGISTERED, ENABLED, DISABLED, UNINSTALLED)"),
):
    """List all installed plugins."""
    async def _list():
        try:
            plugin_registry = await create_plugin_registry(DB_PATH)
            plugins = await plugin_registry.list_descriptors()
            
            if not plugins:
                typer.echo("No plugins installed.")
                return
            
            if status:
                try:
                    filter_status = PluginStatus[status.upper()]
                    plugins = [p for p in plugins if p.status == filter_status]
                except KeyError:
                    typer.echo(f"Invalid status: {status}", err=True)
                    raise typer.Exit(1)
            
            typer.echo(f"Plugins ({len(plugins)}):")
            for p in plugins:
                typer.echo(f"  - {p.manifest.name} v{p.manifest.version} [{p.status.value}] ID: {p.manifest.id}")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    
    asyncio.run(_list())


@plugin_app.command("enable")
def plugin_enable(
    plugin_id: str = typer.Argument(..., help="Plugin ID to enable"),
):
    """Enable a registered plugin."""
    async def _enable():
        try:
            plugin_registry = await create_plugin_registry(DB_PATH)
            await plugin_registry.enable(plugin_id)
            typer.echo(f"Plugin {plugin_id} enabled")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    
    asyncio.run(_enable())


@plugin_app.command("disable")
def plugin_disable(
    plugin_id: str = typer.Argument(..., help="Plugin ID to disable"),
):
    """Disable an enabled plugin."""
    async def _disable():
        try:
            plugin_registry = await create_plugin_registry(DB_PATH)
            await plugin_registry.disable(plugin_id)
            typer.echo(f"Plugin {plugin_id} disabled")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    
    asyncio.run(_disable())


@plugin_app.command("uninstall")
def plugin_uninstall(
    plugin_id: str = typer.Argument(..., help="Plugin ID to uninstall"),
):
    """Uninstall a plugin completely."""
    async def _uninstall():
        try:
            plugin_registry = await create_plugin_registry(DB_PATH)
            await plugin_registry.uninstall(plugin_id)
            typer.echo(f"Plugin {plugin_id} uninstalled")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    
    asyncio.run(_uninstall())


@plugin_app.command("discover")
def plugin_discover(
    path: str = typer.Argument(
        "plugins",
        help="Directory to discover plugins from (default: plugins/)",
    ),
):
    """Discover and auto-install plugins from a directory."""
    async def _discover():
        try:
            plugin_registry = await create_plugin_registry(DB_PATH)
            plugin_discovery = await create_plugin_discovery(DB_PATH, plugin_registry)
            
            plugin_ids = await plugin_discovery.discover_from_directory(Path(path))
            
            if not plugin_ids:
                typer.echo(f"No plugins found in {path}")
                return
            
            typer.echo(f"Discovered and installed {len(plugin_ids)} plugin(s) from {path}:")
            for pid in plugin_ids:
                descriptor = await plugin_registry.get_descriptor(pid)
                if descriptor:
                    typer.echo(f"  - {descriptor.manifest.name} v{descriptor.manifest.version} [{descriptor.status.value}] (ID: {pid})")
                else:
                    typer.echo(f"  - Plugin {pid} (descriptor not found)")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    
    asyncio.run(_discover())


@plugin_app.command("upgrade")
def plugin_upgrade(
    plugin_id: str = typer.Argument(..., help="Plugin ID to upgrade"),
    manifest_path: str = typer.Argument(..., help="Path to new manifest.yaml"),
    force: bool = typer.Option(False, "--force", help="Allow major version upgrade without confirmation"),
):
    """Upgrade a plugin with a new manifest (version must be greater).

    Major version upgrade (1.x -> 2.x) requires --force flag.
    On failure, automatically rolls back to old manifest.
    """
    async def _upgrade():
        try:
            loader = PluginManifestLoader()
            m_path = Path(manifest_path)
            if not m_path.exists():
                typer.echo(f"Manifest not found: {manifest_path}", err=True)
                raise typer.Exit(1)

            new_manifest = loader.load_from_yaml(m_path)
            if not new_manifest:
                typer.echo(f"Failed to parse manifest: {manifest_path}", err=True)
                raise typer.Exit(1)

            # Ensure the manifest is a PluginManifest instance
            if not isinstance(new_manifest, PluginManifest):
                new_manifest = PluginManifest(**new_manifest)

            plugin_registry = await create_plugin_registry(DB_PATH)
            mgr = PluginLifecycleManager(plugin_registry)

            result_id = await mgr.upgrade(plugin_id, new_manifest, force=force)

            descriptor = await plugin_registry.get_descriptor(result_id)
            if descriptor:
                typer.echo(
                    f"Upgraded plugin: {descriptor.manifest.name} "
                    f"v{descriptor.manifest.version} "
                    f"[{descriptor.status.value}]"
                )
            else:
                typer.echo(f"Plugin {result_id} upgraded successfully")

        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Unexpected error: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_upgrade())


@plugin_app.command("health")
def plugin_health(
    plugin_id: str = typer.Argument(None, help="Plugin ID to check (optional, checks all if omitted)"),
):
    """Check health of a plugin or all plugins."""
    async def _health():
        try:
            plugin_registry = await create_plugin_registry(DB_PATH)
            from sam.plugin import PluginHealthChecker
            checker = PluginHealthChecker(plugin_registry)
            
            if plugin_id:
                # Check single plugin
                result = await checker.check(plugin_id)
                typer.echo(f"Plugin: {result.plugin_id}")
                typer.echo(f"  Status: {result.status}")
                typer.echo(f"  Version: {result.version}")
                typer.echo(f"  Capabilities: {', '.join(result.capabilities) if result.capabilities else 'none'}")
                typer.echo(f"  Last Check: {result.last_check.isoformat()}")
                if result.message:
                    typer.echo(f"  Message: {result.message}")
            else:
                # Check all plugins
                results = await checker.check_all()
                if not results:
                    typer.echo("No plugins registered.")
                    return
                
                typer.echo(f"Health status for {len(results)} plugin(s):")
                for pid, status in results.items():
                    typer.echo(f"  - {pid}: {status.status} (v{status.version}) {', '.join(status.capabilities) if status.capabilities else 'no capabilities'}")
                    if status.message:
                        typer.echo(f"      {status.message}")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    
    asyncio.run(_health())


# Daemon management commands
daemon_app = typer.Typer()
app.add_typer(daemon_app, name="daemon")


# Global daemon reference for start/stop lifecycle across commands
_daemon_instance: Optional[RuntimeDaemon] = None
_daemon_task: Optional[asyncio.Task] = None


def _get_daemon() -> RuntimeDaemon:
    """Get or create a daemon instance with default services."""
    global _daemon_instance
    if _daemon_instance is None:
        event_bus = EventBus()
        job_queue = JobQueue(event_bus)
        scheduler = Scheduler(job_queue, event_bus)
        notification = NotificationService(event_bus)

        config = DaemonConfig(
            poll_interval=5.0,
            shutdown_timeout=30.0,
            health_check_interval=60.0,
        )

        _daemon_instance = RuntimeDaemon(
            config=config,
            event_bus=event_bus,
            services=[scheduler, notification],
        )
    return _daemon_instance


@daemon_app.command("start")
def daemon_start():
    """Start the runtime daemon in the foreground."""
    async def _start():
        global _daemon_instance, _daemon_task
        try:
            daemon = _get_daemon()

            if daemon.running:
                typer.echo("Daemon is already running.")
                return

            typer.echo("Starting daemon...")
            await daemon.start()

            # Run forever in background task
            _daemon_task = asyncio.create_task(daemon.run_forever())

            health = await daemon.health()
            dh = health.get("daemon")
            if dh:
                typer.echo(f"Daemon started: {dh.status.value} ({dh.message})")
            for name, h in health.items():
                if name == "daemon":
                    continue
                typer.echo(f"  - {name}: {h.status.value}")

        except Exception as e:
            typer.echo(f"Error starting daemon: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_start())


@daemon_app.command("stop")
def daemon_stop():
    """Stop the runtime daemon."""
    async def _stop():
        global _daemon_instance, _daemon_task
        if _daemon_instance is None or not _daemon_instance.running:
            typer.echo("Daemon is not running.")
            return

        typer.echo("Stopping daemon...")
        await _daemon_instance.stop(signal_name="CLI")

        if _daemon_task:
            _daemon_task.cancel()
            try:
                await _daemon_task
            except asyncio.CancelledError:
                pass
            _daemon_task = None

        _daemon_instance = None
        typer.echo("Daemon stopped.")

    asyncio.run(_stop())


@daemon_app.command("status")
def daemon_status():
    """Show status of the daemon and its services."""
    async def _status():
        global _daemon_instance
        if _daemon_instance is None:
            typer.echo("Daemon is not running.")
            return

        if not _daemon_instance.running:
            typer.echo("Daemon is registered but not running.")
            return

        health = await _daemon_instance.health()
        dh = health.get("daemon")
        if dh:
            typer.echo(f"Daemon: {dh.status.value}")
            typer.echo(f"  Message: {dh.message}")
            typer.echo(f"  Last Check: {dh.last_check.isoformat()}")

        for name, h in health.items():
            if name == "daemon":
                continue
            typer.echo(f"  - {name}: {h.status.value}")
            if h.message:
                typer.echo(f"      {h.message}")
            if h.metrics:
                for k, v in h.metrics.items():
                    typer.echo(f"      {k}: {v}")

    asyncio.run(_status())


@daemon_app.command("health")
def daemon_health():
    """Show health of all daemon services."""
    async def _health():
        global _daemon_instance
        if _daemon_instance is None or not _daemon_instance.running:
            typer.echo("Daemon is not running.")
            return

        health = await _daemon_instance.health()
        typer.echo(f"Daemon Health ({len(health)} services):")
        for name, h in health.items():
            typer.echo(f"  {name}:")
            typer.echo(f"    Status: {h.status.value}")
            typer.echo(f"    Message: {h.message}")
            typer.echo(f"    Last Check: {h.last_check.isoformat()}")
            if h.metrics:
                typer.echo(f"    Metrics: {h.metrics}")

    asyncio.run(_health())


# ── Cluster management commands ────────────────────────────────────────

cluster_app = typer.Typer()
app.add_typer(cluster_app, name="cluster")


@cluster_app.command("status")
def cluster_status(
    format: str = typer.Option("table", "--format", "-f", help="Output format: table or json"),
):
    """Show cluster state and health."""
    async def _status():
        try:
            from sam.cluster.state import ClusterStateAggregator
            from sam.cluster.node_registry import NodeRegistry
            from sam.cluster.leader import LeaderElection
            from sam.core.job_queue import JobQueue
            from sam.core.event_bus import EventBus
            from sam.core.daemon import DaemonConfig

            config = DaemonConfig()

            # Setup minimal components for state collection
            event_bus = EventBus()
            job_queue = JobQueue(event_bus)
            node_registry = NodeRegistry()

            # LeaderElection needs a DB — skip for CLI; pass a none-like
            # We create a lightweight leader election with no DB backing
            leader_election = LeaderElection(None, config.cluster_id)  # type: ignore[arg-type]

            aggregator = ClusterStateAggregator(
                node_registry=node_registry,
                job_queue=job_queue,
                leader_election=leader_election,
                cluster_id=config.cluster_id,
            )

            state = await aggregator.collect()

            if format == "json":
                import json
                typer.echo(json.dumps(state.to_dict(), indent=2, default=str))
            else:
                # Table format
                typer.echo(f"\nCluster: {state.cluster_id}")
                typer.echo(f"Updated : {state.updated_at.isoformat()}")
                typer.echo()
                typer.echo(f"  Leader: {state.leader_id or 'none'}")
                typer.echo(f"  Nodes : {state.node_count} total")
                typer.echo(f"          {state.online_nodes} online")
                typer.echo(f"          {state.offline_nodes} offline")
                typer.echo(f"          {state.degraded_nodes} degraded")
                typer.echo()
                typer.echo(f"  Active Workflows: {state.active_workflows}")
                typer.echo(f"  Jobs (pending/running/failed): {state.pending_jobs}/{state.running_jobs}/{state.failed_jobs}")
                typer.echo()
                typer.echo(f"  Total Load: {state.total_load:.1f}%")

                if state.node_details:
                    typer.echo()
                    typer.echo("Node Details:")
                    for node_id, detail in state.node_details.items():
                        status_emoji = {"ONLINE": "🟢", "OFFLINE": "🔴", "DEGRADED": "🟡"}.get(
                            detail.get("status", ""), "⚪"
                        )
                        typer.echo(
                            f"  {status_emoji} {node_id}"
                            f" | {detail.get('hostname', '?')}"
                            f" | v{detail.get('version', '?')}"
                            f" | load={detail.get('load', 0):.1f}%"
                        )

        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_status())


if __name__ == "__main__":
    app()
