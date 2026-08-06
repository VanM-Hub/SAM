"""LLM Chain Wiring - Program K (Connector Runtime Activation, K1).

Composition root untuk jalur LLM resmi:
    Connector Runtime -> Provider Runtime -> Agent Runtime.

Program K K1 - Connector Runtime Activation:
- MengOPERASIONALKAN Connector Runtime yang SUDAH ADA (connectors/ConnectorRuntime).
- TIDAK membuat Connector Runtime baru.
- TIDAK mengubah semantic Connector Runtime.
- TIDAK mengubah RuntimeService.

Modul ini MENGISI (populate) layer connector baseline yang selama ini dormant
(Sprint 112/121) dengan deskriptor connector LLM declarative. Ini menempatkan
connector baseline LLM ke dalam ConnectorRegistry + ConnectorRuntime sehingga
layer ini AKTIF (bukan konsep baru; engine-nya sudah ada, kita wire datanya).

Kontrak Provider -> Connector dijaga via `ProviderDescriptor.implements`
(link resmi dari provider ke kontrak Connector Runtime), sehingga urutan
Connector -> Provider -> Agent dipertahankan tanpa mengubah dependency rules.

Composition-only: tidak ada business logic; tidak ada network; tidak ada
perubahan host Presentation / RuntimeService.
"""
from __future__ import annotations
from typing import List

# --- Connector Runtime baseline (engine yang SUDAH ADA, di-reuse) ---------- #
from ..connectors.connector_descriptor import ConnectorDescriptor
from ..connectors.connector_capability import ConnectorCapability
from ..connectors.connector_contract import ConnectorContract
from ..connectors.connector_metadata import ConnectorMetadata
from ..connectors.connector_registry import ConnectorRegistry
from ..connectors.runtime import ConnectorRuntime, RuntimeReadiness


# --------------------------------------------------------------------------- #
# Baseline connector LLM (declarative, provider-agnostic).
# Satu kontrak connector dibuat agar provider LLM bisa meng-'implements'.
# --------------------------------------------------------------------------- #
LLM_CONNECTOR_CONTRACT_ID = "connector.llm.chat"


def _llm_connector() -> ConnectorDescriptor:
    return ConnectorDescriptor(
        connector_id="llm_chat",
        name="LLM Chat Connector",
        connector_type="llm",
        version="1.0.0",
        description="Baseline connector untuk jalur LLM: menyalurkan capability "
                    "chat/inference ke Provider Runtime (preview-only, deterministik).",
        tags=["llm", "chat", "baseline"],
    )


def _llm_capabilities(connector_id: str) -> List[ConnectorCapability]:
    return [
        ConnectorCapability(
            capability_id=f"{connector_id}.chat",
            connector_id=connector_id,
            name="chat",
            category="llm",
            description="Chat completion / inference (deterministik, preview-only).",
            supported_operations=["chat", "generate", "complete"],
        ),
        ConnectorCapability(
            capability_id=f"{connector_id}.model_list",
            connector_id=connector_id,
            name="model_list",
            category="llm",
            description="Daftar model yang disediakan provider (read-only).",
            supported_operations=["models"],
        ),
    ]


def _llm_contract(connector_id: str) -> ConnectorContract:
    return ConnectorContract(
        contract_id=LLM_CONNECTOR_CONTRACT_ID,
        connector_id=connector_id,
        name="LLM Chat Contract",
        schema_version="1.0",
        guarantees=["preview-only", "deterministic", "provider-agnostic"],
        constraints=["no-network-on-preview", "external-calls-zero-on-preview"],
    )


def _llm_metadata(connector_id: str) -> ConnectorMetadata:
    # SECURITY: tidak menyimpan credential/API key apapun.
    return ConnectorMetadata(
        metadata_id=f"{connector_id}.meta",
        connector_id=connector_id,
        vendor="SAM",
        category="llm",
        homepage="",
        docs_ref="docs/engineering/program-k",
        extra={"shipped_by": "program_k", "k_stage": "K1"},
    )


# --------------------------------------------------------------------------- #
# Composition: bangun ConnectorRegistry + ConnectorRuntime baseline.
# --------------------------------------------------------------------------- #
class LLMConnectorLayer:
    """Composition root untuk layer Connector jalur LLM (K1).

    Mengisi ConnectorRegistry dengan baseline connector LLM dan mengekspos
    readiness via ConnectorRuntime yang SUDAH ADA (no semantic change).
    """

    def __init__(self) -> None:
        self._registry = ConnectorRegistry()
        self._runtime: ConnectorRuntime | None = None
        self._register_baseline()

    def _register_baseline(self) -> None:
        conn = _llm_connector()
        reg = self._registry
        reg.register(conn)
        for cap in _llm_capabilities(conn.connector_id):
            reg.attach_capability(cap)
        reg.attach_contract(_llm_contract(conn.connector_id))
        reg.attach_metadata(_llm_metadata(conn.connector_id))
        self._runtime = ConnectorRuntime(reg)

    @property
    def registry(self) -> ConnectorRegistry:
        return self._registry

    @property
    def runtime(self) -> ConnectorRuntime:
        if self._runtime is None:
            raise RuntimeError("connector runtime belum dibangun")
        return self._runtime

    def readiness(self) -> RuntimeReadiness:
        return self.runtime.readiness()

    def summary(self) -> dict:
        s = self._registry.summary()
        return {
            "total_connectors": s.total_connectors,
            "registered": s.registered,
            "discovered": s.discovered,
            "by_type": s.by_type,
            "contract": LLM_CONNECTOR_CONTRACT_ID,
        }


# --------------------------------------------------------------------------- #
# K2 - Provider Runtime Activation.
# MengOPERASIONALKAN ProviderExecutor (stub -> HTTP nyata via httpx) dan
# menghubungkannya ke adapter provider yang SUDAH ADA (OpenAI, Anthropic, ...).
# Link Connector -> Provider dijaga via `ProviderDescriptor.implements`.
# --------------------------------------------------------------------------- #
from ..providers.execution.provider_executor import ProviderExecutor
from ..providers.registry.provider_builder import ProviderBuilder
from ..providers.base.provider_descriptor import (
    ProviderDescriptor,
    ProviderStatus,
)
from ..providers.base.provider_capability import (
    ProviderCapability,
    ProviderOperation,
)
from ..providers.base.provider_contract import ProviderContract
from ..providers.base.base_provider import BaseProvider
from ..providers.openai.openai_provider import OpenAIAdapter
from ..providers.anthropic.anthropic_provider import AnthropicAdapter
from ..providers.gemini.gemini_provider import GeminiAdapter
from ..providers.deepseek.deepseek_provider import DeepSeekAdapter
from ..providers.ollama.ollama_provider import OllamaAdapter


class _BaseLLMProvider(BaseProvider):
    """Provider base declarative (Phase XIV style) untuk adapter LLM yang ADA."""

    def __init__(self, adapter: object) -> None:
        super().__init__()
        self._adapter = adapter
        pid = getattr(adapter, "provider_id", "unknown")
        self.descriptor = ProviderDescriptor(
            provider_id=pid,
            name=f"{pid} provider",
            provider_type=pid,
            version="1.0.0",
            description=f"Provider {pid} (adapter yang sudah ada).",
            tags=["llm", pid],
            implements=[LLM_CONNECTOR_CONTRACT_ID],
        )
        self.capabilities = [
            ProviderCapability(
                capability_id=f"{pid}.chat",
                provider_id=pid,
                name="chat",
                category="llm",
                operations=[
                    ProviderOperation("chat", "chat completion"),
                    ProviderOperation("models", "list models"),
                ],
            )
        ]
        self.contract = ProviderContract(
            contract_id=LLM_CONNECTOR_CONTRACT_ID,
            provider_id=pid,
            name="LLM Chat Contract",
            guarantees=["preview-only", "deterministic"],
            constraints=["no-network-on-preview"],
        )


class LLMProviderLayer:
    """Composition root untuk layer Provider jalur LLM (K2).

    - Mengoperasionalkan ProviderExecutor (stub -> HTTP nyata via httpx).
    - Menghubungkannya ke adapter provider yang SUDAH ADA (intra layer).
    - Mendaftarkan provider ke ProviderRegistry via ProviderBuilder dengan
      `implements=<connector contract>` (link resmi Connector -> Provider).
    - TIDAK mengubah arsitektur, TIDAK menambah konsep provider baru.
    """

    def __init__(self) -> None:
        self._registry: object | None = None
        self._builder = ProviderBuilder()
        self._provider_executor = ProviderExecutor()
        self._register_adapters()
        self._build_registry()

    def _register_adapters(self) -> None:
        adapters = {
            OpenAIAdapter().provider_id: OpenAIAdapter(),
            AnthropicAdapter().provider_id: AnthropicAdapter(),
            GeminiAdapter().provider_id: GeminiAdapter(),
            DeepSeekAdapter().provider_id: DeepSeekAdapter(),
            OllamaAdapter().provider_id: OllamaAdapter(),
        }
        for pid, adapter in adapters.items():
            self._provider_executor.register_adapter(pid, adapter)
            self._builder.add(_BaseLLMProvider(adapter))

    def _build_registry(self) -> None:
        self._registry = self._builder.build()

    @property
    def executor(self) -> ProviderExecutor:
        return self._provider_executor

    @property
    def registry(self) -> object:
        if self._registry is None:
            raise RuntimeError("provider registry belum dibangun")
        return self._registry

    def available(self, provider_id: str) -> bool:
        return self._provider_executor.available(provider_id)

    def list_providers(self) -> list:
        return self.registry.list_ids()

    def summary(self) -> dict:
        s = self.registry.summary()
        return {
            "total_providers": s.total_providers,
            "registered": s.registered,
            "discovered": s.discovered,
            "by_type": s.by_type,
            "contract": LLM_CONNECTOR_CONTRACT_ID,
        }


# --------------------------------------------------------------------------- #
# K3 - Agent Runtime Activation.
# Menghubungkan Provider Runtime ke Agent Runtime baseline. TIDAK mengubah
# semantic Agent Runtime (tetap preview-only, deterministik, external_calls=0),
# TIDAK menjadikan Agent Runtime orchestrator baru, TIDAK mengubah RuntimeService.
# Link Provider -> Agent dijaga via `AgentDescriptor.implements`.
# --------------------------------------------------------------------------- #
from ..agent.runtime.agent_runtime import AgentRuntime, AgentRunResult
from ..agent.foundation.agent_registry import AgentRegistry
from ..agent.foundation.agent_descriptor import AgentDescriptor
from ..agent.foundation.agent_capability import AgentCapability, AgentOperation
from ..agent.foundation.agent_contract import AgentContract


class LLMAgentLayer:
    """Composition root untuk layer Agent jalur LLM (K3)."""

    def __init__(self) -> None:
        self._registry = AgentRegistry()
        self._register_baseline_agent()
        self._runtime = AgentRuntime(self._registry)

    def _register_baseline_agent(self) -> None:
        desc = AgentDescriptor(
            agent_id="mission_agent",
            name="Mission Agent",
            version="1.0.0",
            description="Baseline agent jalur LLM (preview lifecycle).",
            runtime_layer="agent",
            implements=[LLM_CONNECTOR_CONTRACT_ID],
        )
        self._registry.register(desc)
        self._registry.attach_capability(AgentCapability(
            capability_id="mission_agent.lifecycle",
            agent_id="mission_agent",
            name="mission_lifecycle",
            category="lifecycle",
            operations=[
                AgentOperation("plan"), AgentOperation("execute"),
            ],
        ))
        self._registry.attach_contract(AgentContract(
            contract_id=LLM_CONNECTOR_CONTRACT_ID,
            agent_id="mission_agent",
            name="LLM Mission Contract",
            guarantees=["preview-only", "deterministic"],
            constraints=["no-network-on-preview"],
        ))

    @property
    def registry(self) -> AgentRegistry:
        return self._registry

    @property
    def runtime(self) -> AgentRuntime:
        return self._runtime

    def summary(self) -> dict:
        s = self._registry.summary()
        return {
            "total_agents": s.total_agents,
            "states": s.states,
            "impl": LLM_CONNECTOR_CONTRACT_ID,
        }

    def agent_ready(self) -> bool:
        return self._registry.count() >= 1


class AgentBridge:
    """Jembatan wiring: hasil Provider Runtime -> mission AgentRuntime.

    BUKAN runtime baru / orkestrator; hanya memetakan output provider menjadi
    mission agent dan menjalankan AgentRuntime yang SUDAH ADA (preview-only).
    AgentRuntime tidak diubah; external_calls tetap 0 di jalur agent.
    """

    def __init__(self, agent_layer: LLMAgentLayer) -> None:
        self._layer = agent_layer

    def run_mission_from_provider(self, provider_id: str,
                                  mission_id: str) -> AgentRunResult:
        runtime = self._layer.runtime
        runtime.register_runtimes(["provider"])
        runtime.enqueue_route([provider_id])
        runtime.machine.create(mission_id)
        runtime.build_plan(f"plan-{mission_id}", mission_id)
        return runtime.run_mission(mission_id)


# Instance composition root (module-level, konsisten pola Program J).
llm_connector_layer: LLMConnectorLayer = LLMConnectorLayer()
llm_provider_layer: LLMProviderLayer = LLMProviderLayer()
llm_agent_layer: LLMAgentLayer = LLMAgentLayer()
llm_agent_bridge: AgentBridge = AgentBridge(llm_agent_layer)


def connector_readiness() -> dict:
    """Readiness Connector Runtime (untuk verifikasi K1 / K6)."""
    r = llm_connector_layer.readiness()
    return {
        "ready": r.ready,
        "checks": [
            {"stage": c.stage, "ok": c.ok, "detail": c.detail}
            for c in r.checks
        ],
    }


def provider_activation() -> dict:
    """Status aktivasi Provider Runtime (K2): daftar provider + ketersediaan.

    Network TIDAK dilakukan di sini; hanya cek kredensial (available).
    """
    registry = llm_provider_layer.registry
    rows = []
    for pid in registry.list_ids():
        desc = registry.get(pid)
        rows.append({
            "provider_id": pid,
            "provider_type": desc.provider_type if desc else "unknown",
            "implements": list(desc.implements) if desc else [],
            "available": llm_provider_layer.available(pid),
        })
    return {
        "contract": LLM_CONNECTOR_CONTRACT_ID,
        "providers": rows,
    }


def agent_activation() -> dict:
    """Status aktivasi Agent Runtime (K3).

    Network TIDAK dilakukan; hanya metadata/capability/contract agent.
    """
    registry = llm_agent_layer.registry
    rows = []
    for aid in registry.list_ids():
        desc = registry.get(aid)
        caps = registry.get_capabilities(aid)
        rows.append({
            "agent_id": aid,
            "runtime_layer": desc.runtime_layer if desc else "unknown",
            "implements": list(desc.implements) if desc else [],
            "capabilities": [c.name for c in caps],
        })
    return {
        "contract": LLM_CONNECTOR_CONTRACT_ID,
        "agents": rows,
    }


# --------------------------------------------------------------------------- #
# K4 - Provider Activation (readiness + dokumentasi status per provider).
# Provider baseline yang SUDAH TERSEDIA (punya LLMAdapter) diaktifkan & aktif
# di `llm_provider_layer`. Provider yang BELUM LENGKAP (tidak punya LLMAdapter
# untuk jalur chat LLM: openclaw, filesystem, shell, sqlite, docker)
# DIDOKUMENTASIKAN sebagai missing/deferred - bukan error, bukan konsep baru.
# --------------------------------------------------------------------------- #
# Status per provider baseline (`PROVIDER_ENV` dari ProviderExecutor):
#   - openai/anthropic/gemini/deepseek/ollama : adapter LLM LENGKAP -> active.
#   - openclaw/filesystem/shell/sqlite/docker : TIDAK punya LLMAdapter untuk
#     jalur chat; keberadaan mereka di PROVIDER_ENV bersifat runtime non-LLM.
#     Untuk jalur LLM, status = missing/deferred (tanpa adapter, tanpa konsep
#     baru; didokumentasikan, provider lain tetap lanjut).
_PROVIDER_LLM_ADAPTERS = {"openai", "anthropic", "gemini", "deepseek", "ollama"}
_PROVIDER_NON_LLM = {"openclaw", "filesystem", "shell", "sqlite", "docker"}


def provider_readiness() -> dict:
    """Status aktivasi seluruh provider baseline (K4).

    Hanya cek kredensial + keberadaan adapter (tidak ada network).
    - status 'active'  : adapter ada & terhubung (available tergantung env).
    - status 'missing' : tidak punya LLMAdapter untuk jalur chat -> didokumentasikan
      deferred; provider lain diaktifkan.
    """
    rows = []
    for pid in sorted(_PROVIDER_LLM_ADAPTERS | _PROVIDER_NON_LLM):
        if pid in _PROVIDER_LLM_ADAPTERS:
            row = {
                "provider_id": pid,
                "adapter": True,
                "status": "active",
                "available": llm_provider_layer.available(pid),
                "note": "LLMAdapter tersedia; eksekusi nyata saat env kredensial diset",
            }
        else:
            row = {
                "provider_id": pid,
                "adapter": False,
                "status": "missing",
                "available": False,
                "note": "tanpa LLMAdapter untuk jalur chat; didokumentasikan (deferred)",
            }
        rows.append(row)
    active = sum(1 for r in rows if r["status"] == "active")
    missing = sum(1 for r in rows if r["status"] == "missing")
    return {
        "contract": LLM_CONNECTOR_CONTRACT_ID,
        "total": len(rows),
        "active": active,
        "missing_documented": missing,
        "providers": rows,
    }
