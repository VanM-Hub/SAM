# Workspace API - IP-3.5-001 (AO-ENG-001, MISSION-3.5)
# WP-07: facade baca-saja (read/mostly-read) untuk seluruh domain Platform
#        Workspace. Titik masuk bagi presentation/UI untuk menyusun workspace.
#
# Bound context: src/sam/platform/ (consumer-only).
# Guardrail (IP-3.5, roadmap SAM 3.5): API bersifat READ-ONLY / penyajian.
#   TIDAK ada: execute, orchestrate, coordinate runtime, modify capability,
#   perform governance/approval, bypass runtime service, new authority.
#   Workspace API PRESENTS; never performs.

"""Workspace API (Facade).

Facade read/assemble-only untuk Platform Workspace. Menyusun pandangan
terpadu (model, perspective, navigasi, konteks, layout, descriptor) bagi
presentation layer. Tidak mengeksekusi, tidak mengubah otoritas/capability,
tidak mengendalikan runtime.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sam.platform.workspace_model import (
    Perspective,
    PerspectiveBinding,
    PlatformDomain,
    WorkspaceModel,
    build_domain,
    build_perspective,
)
from sam.platform.navigation import (
    NavigationModel,
    NavigationRoute,
    build_navigation,
)
from sam.platform.perspective import PerspectiveRegistry, PerspectiveState
from sam.platform.context import WorkspaceContext, ContextStore
from sam.platform.layout import LayoutModel, PanelSlot
from sam.platform.descriptor import WorkspaceDescriptor, descriptor_from_model


@dataclass(frozen=True)
class WorkspaceSnapshot:
    """Snapshot baca-saja dari status tampilan workspace.

    Immutable. Menyajikan apa yang tampil; tidak memegang otoritas apa pun.
    """

    model_name: str
    model_version: str
    active_perspective: str
    domains: Tuple[str, ...]
    perspectives: Tuple[str, ...]
    context: WorkspaceContext
    layout: LayoutModel


class WorkspaceAPI:
    """Facade read-only untuk Platform Workspace.

    Tujuan: menyediakan akses baca-saja & deterministik ke seluruh model
    workspace bagi presentation layer. DILARANG melakukan eksekusi,
    orchestration, koordinasi runtime, atau modifikasi capability.
    """

    def __init__(
        self,
        model: WorkspaceModel,
        navigation: Optional[NavigationModel] = None,
        layout: Optional[LayoutModel] = None,
        source_packages: Tuple[str, ...] = (),
    ) -> None:
        if model is None:
            raise ValueError("model wajib diisi.")
        self._model = model
        self._navigation = navigation or NavigationModel()
        self._layout = layout or LayoutModel(layout_id="default")
        self._descriptor = descriptor_from_model(
            model, source_packages=source_packages
        )
        self._perspective_registry = PerspectiveRegistry(
            perspectives=model.perspective_keys(),
            display_order=model.perspective_keys(),
        )
        self._context_store = ContextStore()

    # --- Informasi (read-only) ----------------------------------------------

    @property
    def model(self) -> WorkspaceModel:
        """Model platform terpadu (read-only referensi)."""
        return self._model

    @property
    def descriptor(self) -> WorkspaceDescriptor:
        """Descriptor workspace (deklaratif)."""
        return self._descriptor

    @property
    def navigation(self) -> NavigationModel:
        return self._navigation

    @property
    def layout(self) -> LayoutModel:
        return self._layout

    def domains(self) -> Tuple[str, ...]:
        """Seluruh domain view yang tersedia (deterministik)."""
        return self._model.domain_keys()

    def perspectives(self) -> Tuple[str, ...]:
        """Perspective yang tersedia, urut untuk navigasi (deterministik)."""
        return self._perspective_registry.ordered()

    def domain(self, key: str) -> Optional[PlatformDomain]:
        return self._model.domain(key)

    def perspective(self, key: str) -> Optional[Perspective]:
        return self._model.perspective(key)

    def routes_for_domain(self, domain: str) -> Tuple[NavigationRoute, ...]:
        return self._navigation.routes_for_domain(domain)

    # --- Konteks tampilan (deklaratif, bukan eksekusi) ----------------------

    def context_for(self, slot_id: str) -> WorkspaceContext:
        """Konteks tampilan saat ini untuk slot.

        Hanya menyimpan kedudukan navigasi/tampilan; tidak menyimpan
        otoritas atau kontrol.
        """
        return self._context_store.get(slot_id)

    def select_perspective(self, slot_id: str, key: str) -> PerspectiveState:
        """Pilih perspective aktif (hanya tampilan).

        Mengubah perspective aktif untuk slot; TIDAK menjalankan apa pun.
        """
        current = self._context_store.get(slot_id)
        new_state = PerspectiveState(
            active=key,
            default=self._perspective_registry.ordered()[0]
            if self._perspective_registry.ordered()
            else "overview",
            available=self._perspective_registry.ordered(),
        ).select(key)
        # Suruh catat perspective ke konteks (immutable).
        updated = WorkspaceContext(perspective=new_state.active)
        self._context_store.set(slot_id, updated)
        return new_state

    def snapshot(self, slot_id: str = "default") -> WorkspaceSnapshot:
        """Snapshot baca-saja kondisi workspace untuk penyajian."""
        ctx = self._context_store.get(slot_id)
        return WorkspaceSnapshot(
            model_name=self._model.name,
            model_version=self._model.version,
            active_perspective=ctx.perspective,
            domains=self._model.domain_keys(),
            perspectives=self._perspective_registry.ordered(),
            context=ctx,
            layout=self._layout,
        )


# --- Factory -----------------------------------------------------------------

def default_workspace(name: str = "SAM Platform") -> WorkspaceAPI:
    """Bangun workspace default yang menyatukan seluruh domain view platform.

    Domain & perspective didefinisikan deklaratif; tidak mengeksekusi apa pun.
    """
    model = WorkspaceModel(name=name, version="1.0.0")
    for dom in (
        PlatformDomain("mission", "Mission", "Mission-centric workflow", "sam.mission", 1),
        PlatformDomain("governance", "Governance", "Governance intelligence", "sam.governance_intelligence", 2),
        PlatformDomain("runtime", "Runtime", "Autonomous runtime", "sam.autonomy_runtime", 3),
        PlatformDomain("citizen", "Citizen", "Citizen ecosystem", "sam.citizen", 4),
        PlatformDomain("federation", "Federation", "Federation", "sam.citizen.federation", 5),
        PlatformDomain("trust", "Trust", "Trust & interop", "sam.citizen.federation", 6),
        PlatformDomain("capability", "Capability", "Capability explorer", "sam.compliance", 7),
    ):
        model = build_domain(model, dom)

    # Perspective utama.
    for persp in (
        Perspective("overview", "Overview", "", ()),
        Perspective("operations", "Operations", "",
                    (PerspectiveBinding("mission", "overview"),
                     PerspectiveBinding("runtime", "health"),
                     PerspectiveBinding("governance", "overview"))),
        Perspective("mission", "Mission", "",
                    (PerspectiveBinding("mission", "overview"),
                     PerspectiveBinding("capability", "overview"))),
        Perspective("governance", "Governance", "",
                    (PerspectiveBinding("governance", "overview"),
                     PerspectiveBinding("trust", "overview"),
                     PerspectiveBinding("capability", "overview"))),
        Perspective("ecosystem", "Ecosystem", "",
                    (PerspectiveBinding("citizen", "overview"),
                     PerspectiveBinding("federation", "overview"),
                     PerspectiveBinding("trust", "overview"))),
    ):
        model = build_perspective(model, persp)

    nav = build_navigation(
        (
            NavigationRoute("root", label="Home"),
            NavigationRoute("mission", domain="mission", perspective="mission", label="Mission", parent="root"),
            NavigationRoute("governance", domain="governance", perspective="governance", label="Governance", parent="root"),
            NavigationRoute("runtime", domain="runtime", perspective="overview", label="Runtime", parent="root"),
            NavigationRoute("ecosystem", domain="federation", perspective="ecosystem", label="Ecosystem", parent="root"),
        )
    )

    layout = LayoutModel(
        layout_id="default",
        regions=("header", "main", "aside", "footer"),
        panels=(
            PanelSlot("nav", "header", domain="capability", priority=10),
            PanelSlot("main", "main", domain="mission", priority=100),
            PanelSlot("context", "aside", domain="capability", priority=50),
            PanelSlot("status", "footer", domain="runtime", priority=5),
        ),
    )

    return WorkspaceAPI(
        model=model,
        navigation=nav,
        layout=layout,
        source_packages=(
            "sam.mission",
            "sam.governance_intelligence",
            "sam.autonomy_runtime",
            "sam.citizen",
            "sam.citizen.federation",
            "sam.compliance",
        ),
    )
