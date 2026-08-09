# Citizen & Federation Workspace - IP-3.5-003 (AO-ENG-001, MISSION-3.5)
# WP-17 (Citizen Workspace) + WP-18 (Federation Workspace).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# CAPABILITY BOUNDARY: platform MENERIMA data citizen/federation dari luar
#   (governed capability API / caller) sebagai input. Platform TIDAK mengimpor
#   citizen internal secara deep dan TIDAK memodifikasi citizens/federation.
#   Guardrail MISSION-3.5: "MUST NOT modify citizens". Citizen Experience
#   menyajikan manifest capability; tidak pernah menjalankan aksi citizen.

"""Citizen & Federation Workspace.

Menyajikan pandangan citizen (identity + capability) dan federation (anggota +
interoperabilitas) secara deklaratif. Seluruh data DIBERIKAN sebagai input
dataclass immutable; platform hanya menyusun & menyajikan.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple


# --- Citizen input model (diberikan dari luar) ------------------------------

@dataclass(frozen=True)
class CitizenInput:
    """Data citizen yang DIBERIKAN ke platform untuk penyajian.

    Mencerminkan manifest citizen (identity/kind/name/version/capability).
    Platform tidak menariknya dari registry citizen internal.
    """

    identity_id: str
    kind: str = ""
    name: str = ""
    version: str = ""
    capabilities: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.identity_id or not self.identity_id.strip():
            raise ValueError("identity_id wajib diisi.")


# --- Federation input model (diberikan dari luar) ---------------------------

@dataclass(frozen=True)
class FederationMemberInput:
    """Satu anggota federation yang DIBERIKAN untuk penyajian.

    Deklaratif; platform tidak memodifikasi anggota federation.
    """

    member_id: str
    name: str = ""
    capabilities: Tuple[str, ...] = ()
    trusted: bool = False


@dataclass(frozen=True)
class FederationInput:
    """Ringkasan federation yang DIBERIKAN untuk penyajian.

    Mencerminkan keadaan federation (trusted/untrusted member); observasional.
    """

    federation_id: str
    members: Tuple[FederationMemberInput, ...] = ()

    def trusted_members(self) -> Tuple[FederationMemberInput, ...]:
        return tuple(m for m in self.members if m.trusted)

    def untrusted_members(self) -> Tuple[FederationMemberInput, ...]:
        return tuple(m for m in self.members if not m.trusted)


# --- Presentation views ------------------------------------------------------

@dataclass(frozen=True)
class CitizenWorkspaceView:
    """Pandangan citizen-centric untuk disajikan (immutable)."""

    citizens: Tuple[CitizenInput, ...] = ()

    def citizen(self, identity_id: str) -> Optional[CitizenInput]:
        for c in self.citizens:
            if c.identity_id == identity_id:
                return c
        return None

    def by_kind(self, kind: str) -> Tuple[CitizenInput, ...]:
        return tuple(c for c in self.citizens if c.kind == kind)

    @property
    def count(self) -> int:
        return len(self.citizens)


@dataclass(frozen=True)
class FederationWorkspaceView:
    """Pandangan federation-centric untuk disajikan (immutable)."""

    federations: Tuple[FederationInput, ...] = ()

    def federation(self, federation_id: str) -> Optional[FederationInput]:
        for f in self.federations:
            if f.federation_id == federation_id:
                return f
        return None

    def federation_count(self) -> int:
        return len(self.federations)

    def total_members(self) -> int:
        return sum(len(f.members) for f in self.federations)


def build_citizen_view(citizens: Sequence[CitizenInput]) -> CitizenWorkspaceView:
    """Build citizen view, diurutkan deterministik."""
    return CitizenWorkspaceView(citizens=tuple(sorted(
        citizens, key=lambda c: c.identity_id)))


def build_federation_view(
    federations: Sequence[FederationInput],
) -> FederationWorkspaceView:
    """Build federation view, diurutkan deterministik."""
    return FederationWorkspaceView(federations=tuple(sorted(
        federations, key=lambda f: f.federation_id)))
