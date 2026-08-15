"""Citizen Ecosystem Wiring — composition root (review remediation).

Menutup gap yang ditemukan review: `CitizenRegistry` + `CitizenAPI` sebelumnya
didefinisikan lengkap (identity/registry/descriptor/discovery/api) tetapi TIDAK
pernah di-instantiate/di-wire di aplikasi (0 import dari composition root).
Akibatnya Article IV ("Registry over Direct Dependency") hanya ada di atas
kertas.

Registry di sini MURNI menyimpan identitas + metadata (descriptor) dan melayani
discovery read-only. Registry != Authority (ED-3.3-001): tidak mengaktifkan,
tidak menjalankan capability, tidak mengatur lifecycle.

Citizen yang didaftarkan adalah subsistem NYATA yang dibangun di composition
root (lihat `sam/api/wiring.py`): execution runtime, provider executor,
registry capability (knowledge/workflow/artifact/memory/policy/audit), mission
runtime, capability system, dan REST host. Ini declarative manifest — registry
menyimpan metadata, BUKAN objek runtime itu sendiri.
"""
from __future__ import annotations

from sam.citizen.registry.registry import CitizenRegistry
from sam.citizen.identity.models import CitizenIdentity
from sam.citizen.descriptor.descriptor import build_descriptor
from sam.citizen.api.citizen import CitizenAPI

# --- declarative manifest: (kind, name, version, namespace, summary,
#                            contracts, capabilities) ---
_MANIFEST = (
    ("runtime", "execution-runtime", "1.0", "execution",
     "ExecutionRuntime: jalur eksekusi preview/execute yang approval-gated.",
     ("execution.preview", "execution.approval-gated"),
     ("execution.preview", "execution.governed")),
    ("runtime", "runtime-service", "1.0", "runtime",
     "RuntimeService API: status/health jalur resmi.",
     ("runtime.status", "runtime.health"),
     ("runtime.status",)),
    ("provider", "provider-executor", "1.0", "execution",
     "ProviderExecutor: aktivasi & eksekusi provider (abstraksi provider).",
     ("provider.activation",),
     ("provider.execute",)),
    ("workflow", "workflow-registry", "1.0", "capability",
     "WorkflowRegistry: registry capability workflow.",
     ("workflow.list", "workflow.resolve"),
     ("workflow.list", "workflow.resolve")),
    ("policy", "policy-registry", "1.0", "capability",
     "PolicyRegistry: registry capability policy.",
     ("policy.list", "policy.resolve"),
     ("policy.list", "policy.resolve")),
    ("mission", "mission-runtime", "1.0", "mission",
     "MissionRuntime: membangun & merutekan mission.",
     ("mission.build", "mission.route"),
     ("mission.build",)),
    ("capability", "capability-system", "1.0", "capability",
     "Capability system: model & resolusi capability universal.",
     ("capability.resolve",),
     ("capability.resolve",)),
    ("service", "knowledge-registry", "1.0", "capability",
     "KnowledgeRegistry: registry capability knowledge.",
     ("knowledge.list", "knowledge.resolve"),
     ("knowledge.list", "knowledge.resolve")),
    ("service", "artifact-registry", "1.0", "capability",
     "ArtifactRegistry: registry capability artifact.",
     ("artifact.list", "artifact.resolve"),
     ("artifact.list", "artifact.resolve")),
    ("service", "memory-registry", "1.0", "capability",
     "MemoryRegistry: registry capability memory.",
     ("memory.list", "memory.resolve"),
     ("memory.list", "memory.resolve")),
    ("service", "audit-registry", "1.0", "capability",
     "AuditRegistry: registry capability audit.",
     ("audit.list", "audit.resolve"),
     ("audit.list", "audit.resolve")),
    ("service", "rest-api-host", "1.0", "presentation",
     "RESTApplication: host REST API (presentation layer).",
     ("http.rest",),
     ("http.serve",)),
)


def build_citizen_ecosystem():
    """Bangun registry + descriptor + API (read-only) dari manifest nyata."""
    registry = CitizenRegistry()
    descriptors = {}
    for (kind, name, version, namespace, summary,
         contracts, capabilities) in _MANIFEST:
        identity = CitizenIdentity.new(kind, name, version=version,
                                       namespace=namespace)
        registry.register(identity, origin="composition-root",
                          annotations=(("source", "manifest"),))
        descriptors[identity.identity_id] = build_descriptor(
            identity,
            summary=summary,
            contracts=tuple(contracts),
            capabilities=tuple(capabilities),
            health_status="unknown",
            lifecycle_stage="registered",
        )
    return registry, CitizenAPI(registry, descriptors=descriptors)


# Singleton composition root (dibangun sekali saat import).
citizen_registry, citizen_api = build_citizen_ecosystem()
