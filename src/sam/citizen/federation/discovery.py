# Federation Discovery - WP-03
# IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
#
# Discovery antar Federation.
#
# REGISTRY-BASED: discovery hanya men-cari/mencocokkan metadata dari
# FederationRegistry. BUKAN auto-connect - discovery TIDAK membentuk koneksi,
# tidak menghubungi remote, tidak melakukan handshake. Hasil discovery bersifat
# informasional: "siapa yang dikenal tentang capability X".

from typing import Optional, Sequence, Tuple

from sam.citizen.federation.registry import FederationRegistry


class FederationDiscovery:
    """Penemu anggota Federation berdasarkan registry (read-only)."""

    def __init__(self, registry: FederationRegistry, descriptors=None)\
            -> None:
        self._registry = registry
        self._descriptors = tuple(descriptors or ())

    def _descriptor_caps(self, member_id: str) -> Tuple[str, ...]:
        for d in self._descriptors:
            if getattr(d, "member_id", None) == member_id:
                return tuple(getattr(d, "capability", ()))
        return ()

    def discover_all(self) -> Tuple[str, ...]:
        """Semua member yang dikenal (id saja)."""
        return self._registry.member_ids()

    def discover_by_capability(self, capability: str) -> Tuple[str, ...]:
        """Member yang meng-iklankan capability tertentu (sesuai descriptor)."""
        return tuple(
            mid for mid in self._registry.member_ids()
            if capability in self._descriptor_caps(mid)
        )

    def discover_by_state(self, state: str) -> Tuple[str, ...]:
        """Member dengan status pengenalan tertentu."""
        return tuple(m.member_id for m in self._registry.all()
                     if m.state == state)

    def resolve(self, member_id: str) -> Optional[object]:
        """Ambil deskripsi lengkap seorang member (ada/tidak)."""
        return self._registry.get(member_id)

    def find_contract(self, contract: str) -> Tuple[str, ...]:
        """Member yang menyediakan contract tertentu (deskriptif)."""
        return tuple(
            mid for mid in self._registry.member_ids()
            if contract in self._descriptor_caps(mid)
        )
