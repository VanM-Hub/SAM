# Capability Exchange - WP-05
# IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
#
# Pertukaran Capability antar Federation - ADVERTISEMENT, bukan eksekusi.
#
# "Saya memiliki Capability X."   (benar)
# "Jalankan Capability X."          (DILARANG - remote execution)
#
# Capability exchange menghasilkan representasi apa yang DI-IKLANKAN, bukan
# perintah untuk menjalankan. Tidak ada request/execute/invoke. Hasilnya
# deskriptif & deterministik.

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class CapabilityAdvertisement:
    """Iklan capability seorang Federation member (deklaratif)."""

    member_id: str
    capabilities: Tuple[str, ...] = ()
    contracts: Tuple[str, ...] = ()
    declared: bool = True   # selalu deklarasi, bukan aksi

    def __post_init__(self) -> None:
        object.__setattr__(self, "member_id", self.member_id.strip())
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(self, "contracts", tuple(self.contracts))

    def as_dict(self) -> Dict[str, object]:
        return {
            "member_id": self.member_id,
            "capabilities": list(self.capabilities),
            "contracts": list(self.contracts),
            "declared": self.declared,
        }

    @property
    def is_advertisement(self) -> bool:
        """Iklan, bukan eksekusi."""
        return True

    @property
    def is_execution(self) -> bool:
        return False


class CapabilityExchange:
    """Pemetaan iklan capability member (read-only, deskriptif)."""

    def __init__(self, descriptors) -> None:
        self._descriptors = tuple(descriptors or ())

    def advertises(self, member_id: str) -> CapabilityAdvertisement:
        """Iklan capability seorang member (dari descriptor)."""
        for d in self._descriptors:
            if getattr(d, "member_id", None) == member_id:
                return CapabilityAdvertisement(
                    member_id=member_id,
                    capabilities=tuple(getattr(d, "capability", ())),
                    contracts=tuple(getattr(d, "contracts", ())),
                )
        return CapabilityAdvertisement(member_id=member_id)

    def who_advertises(self, capability: str) -> Tuple[str, ...]:
        """Member yang mengiklankan capability tertentu (deskriptif)."""
        return tuple(d.member_id for d in self._descriptors
                     if capability in getattr(d, "capability", ()))

    def exchanged(self) -> Tuple[CapabilityAdvertisement, ...]:
        """Seluruh iklan yang tersedia (deterministik, urut member_id)."""
        members = sorted({getattr(d, "member_id", "") for d in self._descriptors})
        return tuple(self.advertises(m) for m in members if m)
