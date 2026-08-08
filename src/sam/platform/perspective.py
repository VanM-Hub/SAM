# Perspective Management - IP-3.5-001 (AO-ENG-001, MISSION-3.5)
# WP-03: mengelola perspective operasional platform (operations, governance,
#        mission, citizen, federation, trust) secara deklaratif.
#
# Bound context: src/sam/platform/ (consumer-only).
# Guardrail: Perspective != Governance; Pengelolaan tampilan != Otoritas;
#   Aktifkan perspective != mengaktifkan capability.

"""Perspective Management.

Mengelola himpunan perspective yang tersedia & perspective aktif untuk
penyajian. Perspective pengelolaan murni tentang TAMPILAN, tidak tentang
otoritas atau eksekusi. Default perspective deterministik.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class PerspectiveRegistry:
    """Daftar deklaratif perspective yang tersedia di platform.

    Immutable & deterministik.
    """

    perspectives: Tuple[str, ...] = ()
    # Order displays untuk navigasi (key -> order; deterministik).
    display_order: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        unknown = [k for k in self.display_order if k not in self.perspectives]
        if unknown:
            raise ValueError(
                "display_order merujuk perspective tak dikenal: %r" % (unknown,)
            )

    def has(self, key: str) -> bool:
        return key in self.perspectives

    def ordered(self) -> Tuple[str, ...]:
        """Perspective terurut untuk navigasi (deterministik).

        Yang ada di display_order muncul sesuai urutannya; sisanya diurutkan
        alfabetis setelahnya.
        """
        known = list(self.display_order)
        for p in sorted(self.perspectives):
            if p not in known:
                known.append(p)
        return tuple(known)


@dataclass(frozen=True)
class PerspectiveState:
    """Keadaan perspective aktif untuk penyajian.

    Immutable; mengelola tampilan, bukan mengeksekusi.
    """

    active: str = "overview"
    default: str = "overview"
    available: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.available and self.active not in self.available:
            raise ValueError(
                "active %r tidak ada di available %r"
                % (self.active, self.available)
            )

    def select(self, key: str) -> "PerspectiveState":
        """Pilih perspective aktif (immutable, kembalikan state baru).

        Hanya mengubah TAMPILAN. Tidak menjalankan apa pun.
        """
        if self.available and key not in self.available:
            # Fallback deterministik ke default.
            return PerspectiveState(
                active=self.default, default=self.default, available=self.available
            )
        return PerspectiveState(
            active=key, default=self.default, available=self.available
        )

    def reset(self) -> "PerspectiveState":
        return PerspectiveState(
            active=self.default, default=self.default, available=self.available
        )
