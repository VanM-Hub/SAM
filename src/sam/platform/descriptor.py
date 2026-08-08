# Workspace Descriptor - IP-3.5-001 (AO-ENG-001, MISSION-3.5)
# WP-06: mendeskripsikan workspace secara deklaratif untuk keperluan
#        discovery & penyajian. Deskriptif, bukan instruktif.
#
# Bound context: src/sam/platform/ (consumer-only).
# Guardrail: Descriptor != Contract Execution; Deklarasi != Otoritas;
#   Discoverable != Controllable.

"""Workspace Descriptor.

Menyediakan metadata deklaratif tentang sebuah platform workspace: identitas,
versi, domain & perspective yang tersedia, serta capability source yang
dikonsumsi. Descriptor bersifat read-only dan tidak pernah mengeksekusi.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class WorkspaceDescriptor:
    """Deskripsi deklaratif sebuah platform workspace.

    Immutable & deterministik. Menjadi "label" untuk discovery.
    """

    workspace_name: str
    workspace_version: str
    model_version: str
    description: str = ""
    # Daftar key domain yang tampil (ordered, deterministic).
    domains: Tuple[str, ...] = ()
    # Daftar key perspective yang tampil (ordered, deterministic).
    perspectives: Tuple[str, ...] = ()
    # Sumber package capability yang dikonsumsi (untuk audibilitas).
    source_packages: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.workspace_name or not self.workspace_name.strip():
            raise ValueError("workspace_name wajib diisi.")
        if not self.workspace_version or not self.workspace_version.strip():
            raise ValueError("workspace_version wajib diisi.")

    def has_domain(self, key: str) -> bool:
        return key in self.domains

    def has_perspective(self, key: str) -> bool:
        return key in self.perspectives

    def summary_dict(self) -> Dict[str, object]:
        """Ringkasan deklaratif (deterministik)."""
        return {
            "workspace_name": self.workspace_name,
            "workspace_version": self.workspace_version,
            "model_version": self.model_version,
            "domain_count": len(self.domains),
            "perspective_count": len(self.perspectives),
            "source_package_count": len(self.source_packages),
        }


def descriptor_from_model(
    model,
    source_packages: Tuple[str, ...] = (),
    description: str = "",
) -> WorkspaceDescriptor:
    """Bangun WorkspaceDescriptor dari WorkspaceModel (deterministik).

    Murni turunan; tidak memodifikasi model / capability.
    """
    return WorkspaceDescriptor(
        workspace_name=model.name,
        workspace_version=model.version,
        model_version="1.0.0",
        description=description,
        domains=tuple(sorted(d.key for d in model.domains)),
        perspectives=tuple(sorted(p.key for p in model.perspectives)),
        source_packages=tuple(sorted(source_packages)),
    )
