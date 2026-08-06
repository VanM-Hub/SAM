"""CLI RuntimeService Wiring - Program I (I2).

Menghubungkan CLI (presentation) ke jalur resmi runtime_service.
Gateway `ConversationPreviewGateway` (package runtime_service.api) dan
consumer per-capability DITERIMA via dependency injection dari entry -
presentation TIDAK membuat gateway, TIDAK membangun RuntimeAPI, TIDAK
mengakses Runtime/Registry/Provider/Connector/ExecutionRuntime langsung.

Alur (sesuai Arch Package):
    CLI -> runtime_service(ConversationPreviewGateway) -> RuntimeService
    (single entry) -> Existing Runtime Citizens (preview).

I2 mengubah seluruh akses CLI dari `sam.runtime` / `WebRuntimeService` root
menjadi lewat jalur `runtime_service.api` (status, health, preview per
capability). Approval = pass-through (visualisasi field `approved` saja).
Mission/others TANPA jalur: TIDAK dibuat handler (Deferred/Escalation).
"""
from __future__ import annotations
from typing import Any, Callable, Dict, Optional

# Satu-satunya dependency keluar: package runtime_service (diizinkan Arch Package).
from sam.runtime_service.api import ConversationPreviewGateway

from .commands import CLICommand, CLICommandRegistry, build_command
from .formatter import CLIFormatter
from .application import CLIApplication

__all__ = [
    "CLIRuntimeWiring",
    "wire_cli_runtime",
    "CLI_CORE_COMMANDS",
]


# -- command catalogue (composition) --

def _cap_cmd(name: str, description: str) -> CLICommand:
    return build_command(name, description, requires_runtime=True)


CLI_CORE_COMMANDS = [
    _cap_cmd("workflow", "Preview workflow via jalur resmi"),
    _cap_cmd("policy", "Preview policy via jalur resmi"),
    _cap_cmd("audit", "Preview audit (read-only) via jalur resmi"),
    _cap_cmd("preview", "Preview execution (no execute) via jalur resmi"),
    _cap_cmd("knowledge", "Preview knowledge via jalur resmi"),
    _cap_cmd("memory", "Preview memory via jalur resmi"),
    _cap_cmd("artifact", "Preview artifact via jalur resmi"),
    _cap_cmd("approval", "Pass-through: visualisasi status approved"),
    _cap_cmd("runtime", "Status runtime via RuntimeAPI"),
    _cap_cmd("health", "Status kesehatan runtime via RuntimeAPI"),
    _cap_cmd("status", "Status runtime via RuntimeAPI"),
]


def _make_handler(gateway: ConversationPreviewGateway,
                  kind: str,
                  consumers: Dict[str, Any]) -> Callable[..., Any]:
    """Factory handler per command - memanggil jalur gateway (composition)."""
    api = gateway.api

    # --- jalur resolusi via preview_with_* (butuh consumer inject) ---
    if kind == "workflow":
        wc = consumers.get("workflow")
        kc = consumers.get("knowledge")

        def _workflow(workflow_id: str, execution_id: str,
                      knowledge_id: str = ""):
            return gateway.preview_with_workflow(
                None, wc, workflow_id, execution_id, kc, knowledge_id
            )
        return _workflow

    if kind == "policy":
        pc = consumers.get("policy")

        def _policy(policy_id: str, execution_id: str):
            return gateway.preview_with_policy(None, pc, policy_id, execution_id)
        return _policy

    if kind == "audit":
        ac = consumers.get("audit")

        def _audit(audit_id: str, execution_id: str):
            return gateway.preview_with_audit(None, ac, audit_id, execution_id)
        return _audit

    if kind == "preview":

        def _preview(resource_id: str, execution_id: str, **kwargs):
            # preview execution (no execute) - context kosong, jalur resmi.
            # resource_id diterima untuk contract seragam, tidak dipakai.
            return gateway.preview(None, execution_id=execution_id).as_dict()
        return _preview

    if kind == "knowledge":
        kc = consumers.get("knowledge")

        def _knowledge(knowledge_id: str, execution_id: str, memory_id: str = ""):
            return gateway.preview_with_knowledge(
                None, kc, knowledge_id, execution_id, memory_id
            )
        return _knowledge

    if kind == "memory":
        mc = consumers.get("memory")

        def _memory(memory_id: str, execution_id: str):
            return gateway.preview_with_memory(None, mc, memory_id, execution_id)
        return _memory

    if kind == "artifact":
        ac = consumers.get("artifact")

        def _artifact(artifact_name: str, execution_id: str):
            return gateway.preview_with_artifact(None, ac, artifact_name, execution_id)
        return _artifact

    if kind == "approval":
        ac = consumers.get("audit")

        def _approval(resource_id: str, execution_id: str) -> dict:
            # Approval = pass-through: hanya baca status approved dari outcome.
            # resource_id diterima utk contract seragam; execution_id dipakai.
            outcome = gateway.preview(None, execution_id=execution_id)
            return {"approved": bool(outcome.approved),
                    "mode": outcome.mode,
                    "status": outcome.status}
        return _approval

    # --- jalur runtime/health/status via RuntimeAPI ---
    if kind == "runtime":

        def _runtime(*_a, **_k):
            return api.status().as_dict()
        return _runtime

    if kind == "health":

        def _health(*_a, **_k):
            h = api.health()
            return {"status": h.status,
                    "healthy": h.is_healthy() if hasattr(h, "is_healthy") else None}
        return _health

    if kind == "status":

        def _status(*_a, **_k):
            return api.status().as_dict()
        return _status

    # command tanpa jalur (mission dll.) -> tidak ada handler (Deferred)
    return None


class CLIRuntimeWiring:
    """Wiring CLI -> gateway runtime_service (injected). Read-only/composition."""

    def __init__(self,
                 gateway: ConversationPreviewGateway,
                 registry: CLICommandRegistry,
                 consumers: Optional[Dict[str, Any]] = None) -> None:
        self._gateway = gateway
        self._registry = registry
        self._consumers = consumers if consumers is not None else {}
        self._attach()

    def _attach(self) -> None:
        """Pasang handler per command dari catalogue (composition-only)."""
        for cmd in CLI_CORE_COMMANDS:
            handler = _make_handler(self._gateway, cmd.name, self._consumers)
            if handler is None:
                continue  # command tanpa jalur -> TIDAK di-attach
            # pasang handler ke command existing (immutable ditimpa via new)
            attached = CLICommand(
                name=cmd.name,
                description=cmd.description,
                spec=cmd.spec,
                handler=handler,
            )
            self._registry.register(attached)

    @property
    def gateway(self) -> ConversationPreviewGateway:
        return self._gateway

    def attached(self) -> Dict[str, bool]:
        out: Dict[str, bool] = {}
        for name in self._registry.names():
            cmd = self._registry.get(name)
            out[name] = cmd.handler is not None
        return out

    def as_dict(self) -> dict:
        return {
            "wired": True,
            "via": "runtime_service.api.ConversationPreviewGateway",
            "attached": self.attached(),
        }


def wire_cli_runtime(
    gateway: ConversationPreviewGateway,
    registry: Optional[CLICommandRegistry] = None,
    consumers: Optional[Dict[str, Any]] = None,
) -> CLIRuntimeWiring:
    """Wire CLI ke gateway runtime_service (dependency injection dari entry)."""
    if registry is None:
        registry = CLICommandRegistry()
    return CLIRuntimeWiring(gateway, registry, consumers)
