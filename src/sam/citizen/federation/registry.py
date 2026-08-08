# Federation Registry - WP-02
# IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
#
# Registry seluruh Federation Member.
#
# READ-ONLY: registry hanya METADATA - jelas bukan Control Plane. Registry
# tidak mengontrol node, tidak membentuk koneksi, tidak mengeksekusi apapun.
# Registry hanya mencatat apa yang diketahui/diumumkan tentang anggota.

from typing import Dict, Optional, Tuple

from sam.citizen.federation.identity import FederationMember


class FederationRegistry:
    """Registry Federation Member (read-only, metadata-first).

    Penyimpanan identity members. Akses baca diberi public; operasi tulis
    (`register`, `unregister`) bersifat internal/konfigurasi - TIDAK pernah
    memicu aksi remote, tidak mengontrol node.
    """

    def __init__(self) -> None:
        self._members: Dict[str, FederationMember] = {}

    def register(self, member: FederationMember) -> str:
        """Catat seorang member (metadata hanya). Tidak kontrol node."""
        self._members[member.member_id] = member
        return member.member_id

    def unregister(self, member_id: str) -> bool:
        """Hapus pencatatan member. Tidak mengontrol node."""
        return self._members.pop(member_id, None) is not None

    def get(self, member_id: str) -> Optional[FederationMember]:
        return self._members.get(member_id)

    def all(self) -> Tuple[FederationMember, ...]:
        return tuple(sorted(self._members.values(), key=lambda m: m.member_id))

    def member_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._members.keys()))

    def count(self) -> int:
        return len(self._members)

    def has(self, member_id: str) -> bool:
        return member_id in self._members

    def as_dict(self) -> Dict[str, object]:
        return {
            "member_ids": list(self.member_ids()),
            "count": self.count(),
            "members": [m.as_dict() for m in self.all()],
        }
