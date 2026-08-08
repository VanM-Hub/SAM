# Unified Platform Model - IP-3.5-001 (AO-ENG-001, MISSION-3.5 Platform Experience)
# WP-01: mendeskripsikan seluruh domain capability view platform sebagai
#        kumpulan perspective yang kohesif dan ter-navigasi.
#
# Bound context: src/sam/platform/ (bounded context baru MISSION-3.5).
# Consumer-only: platform MENGONSUMSI capability yang sudah ada; TIDAK
#   memodifikasi governance/runtime/citizen/federation/authority.
# Presentation intent (roadmap SAM 3.5): platform PRESENTS governance,
#   never performs governance. Model ini murni deklaratif/deskriptif.
#
# Guardrail (self-verification AO-ENG-001):
#   Model != Execution; View != Control; Domain != Authority;
#   Perspective != Governance.
# DTO immutable, deterministik, ASCII-clean, Python 3.8.

"""Unified Platform Model.

Mendeskripsikan topologi domain capability view yang disatukan platform.
Setiap elemen bersifat deklaratif (mendeskripsikan apa yang ADA), bukan
instruktif (bukan memerintah/mengeksekusi). Model mengelompokkan capability
yang sudah ada ke dalam perspective terpadu untuk presentasi yang konsisten.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# --- Domain identity ---------------------------------------------------------

@dataclass(frozen=True)
class PlatformDomain:
    """Sebuah domain capability yang disatukan ke dalam platform.

    Bersifat deklaratif: mengidentifikasi domain, bukan menjalankannya.
    """

    key: str
    label: str
    description: str = ""
    # Sumber package yang menyediakan domain ini (untuk audibilitas).
    source_package: str = ""
    # Urutan tampilan default (deterministik, bukan eksekusi).
    order: int = 0

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise ValueError("PlatformDomain.key wajib diisi.")
        if not self.label or not self.label.strip():
            raise ValueError("PlatformDomain.label wajib diisi.")


# --- Perspective -------------------------------------------------------------

@dataclass(frozen=True)
class PerspectiveBinding:
    """Mengikat sebuah domain ke sebuah perspective.

    Binding bersifat deklaratif: perspective menampilkan domain, tidak
    memiliki/menjalankan domain.
    """

    domain: str
    # Peran domain dalam perspective (mis. "overview", "detail", "health").
    role: str = "overview"


@dataclass(frozen=True)
class Perspective:
    """Sebuah perspective (sudut pandang) operasional platform.

    Perspective mengelompokkan beberapa domain ke display terpadu.
    Perspective TIDAK pernah melakukan aksi; ia mengatur penyajian.
    """

    key: str
    label: str
    description: str = ""
    bindings: Tuple[PerspectiveBinding, ...] = ()

    def domain_keys(self) -> Tuple[str, ...]:
        """Urutan domain yang terikat (deterministik)."""
        return tuple(sorted(b.domain for b in self.bindings))

    def roles_for(self, domain: str) -> Tuple[str, ...]:
        """Seluruh peran domain dalam perspective (deterministik)."""
        return tuple(
            sorted(b.role for b in self.bindings if b.domain == domain)
        )


# --- Workspace model ---------------------------------------------------------

@dataclass(frozen=True)
class WorkspaceModel:
    """Model platform terpadu: himpunan domain + perspective yang kohesif.

    Model bersifat immutable & deterministik. Ia mendeskripsikan apa yang
    platform tampilkan, bukan apa yang platform lakukan.
    """

    name: str
    version: str = "1.0.0"
    domains: Tuple[PlatformDomain, ...] = ()
    perspectives: Tuple[Perspective, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("WorkspaceModel.name wajib diisi.")

    def domain(self, key: str) -> Optional[PlatformDomain]:
        """Cari domain berdasarkan key (deterministik)."""
        for d in self.domains:
            if d.key == key:
                return d
        return None

    def perspective(self, key: str) -> Optional[Perspective]:
        """Cari perspective berdasarkan key (deterministik)."""
        for p in self.perspectives:
            if p.key == key:
                return p
        return None

    def domain_keys(self) -> Tuple[str, ...]:
        """Seluruh key domain, urut (deterministik)."""
        return tuple(sorted(d.key for d in self.domains))

    def perspective_keys(self) -> Tuple[str, ...]:
        """Seluruh key perspective, urut berdasarkan display order lalu key.

        Deterministik (tidak bergantung urutan masukan).
        """
        return tuple(
            p.key
            for p in sorted(
                self.perspectives,
                key=lambda p: (p.label, p.key),
            )
        )

    def domains_for(self, perspective_key: str) -> Tuple[str, ...]:
        """Domain yang tampil dalam perspective (urutan display)."""
        p = self.perspective(perspective_key)
        if p is None:
            return ()
        return p.domain_keys()


def build_domain(model: WorkspaceModel, domain: PlatformDomain) -> WorkspaceModel:
    """Tambahkan domain secara immutable ke model, kembalikan model baru.

    Domain duplikat (key sama) ditolak.
    """
    if model.domain(domain.key) is not None:
        raise ValueError("Duplikat PlatformDomain key=%r." % domain.key)
    return WorkspaceModel(
        name=model.name,
        version=model.version,
        domains=model.domains + (domain,),
        perspectives=model.perspectives,
    )


def build_perspective(
    model: WorkspaceModel, perspective: Perspective
) -> WorkspaceModel:
    """Tambahkan perspective secara immutable ke model, kembalikan model baru.

    Perspective duplikat (key sama) ditolak.
    """
    if model.perspective(perspective.key) is not None:
        raise ValueError("Duplikat Perspective key=%r." % perspective.key)
    # Validasi: semua binding harus menunjuk ke domain yang terdaftar.
    for b in perspective.bindings:
        if model.domain(b.domain) is None:
            raise ValueError(
                "Perspective %r menunjuk domain tak dikenal %r."
                % (perspective.key, b.domain)
            )
    return WorkspaceModel(
        name=model.name,
        version=model.version,
        domains=model.domains,
        perspectives=model.perspectives + (perspective,),
    )
