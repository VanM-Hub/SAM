# Distributed Knowledge Exchange - WP-23
# IP-3.4-003 (AO-3.4-001, paket ketiga - Distributed Governance Intelligence)
#
# Pertukaran KNOWLEDGE read-only antar federation.
#
# Guardrail IP-3.4-003:
#   Knowledge != Authority (DGI-01)
#   Sovereignty preserved (DGI-06)
#   No hidden dependency (DGI-10)
#
# Knowledge = artefak baca-saja (kontrak, capability, kondisi, pelajaran).
# Dipertukarkan sebagai INFORMASI, bukan sebagai otoritas. Penerima bebas
# menilai sendiri; knowledge tidak memaksa keputusan apa pun.
#
# TIDAK ada koneksi jaringan (no socket/requests/urllib/http.client),
# TIDAK ada sinkronisasi state, TIDAK ada eksekusi remote.

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class KnowledgeArtifact:
    """Satu artefak knowledge yang boleh dipertukarkan (read-only)."""

    source_id: str
    kind: str
    key: str
    value: str
    scope: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "kind": self.kind,
            "key": self.key,
            "value": self.value,
            "scope": list(self.scope),
        }


@dataclass(frozen=True)
class KnowledgePackage:
    """Kumpulan knowledge yang dibagikan satu sumber (read-only)."""

    source_id: str
    artifacts: Tuple[KnowledgeArtifact, ...]
    is_authority: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "artifacts": [a.as_dict() for a in self.artifacts],
            "is_authority": self.is_authority,
        }


class DistributedKnowledgeExchange:
    """Menyusun knowledge packages & membaca knowledge from source (read-only).

    Penyedia memasok artefak; konsumen menerima dan membaca. Tidak ada
    transport jaringan (fungsi murni / in-memory DTO). is_authority selalu
    False - knowledge yang dibagikan tidak pernah menjadi otoritas.
    """

    def package(
        self,
        source_id: str,
        artifacts: Tuple[KnowledgeArtifact, ...],
    ) -> KnowledgePackage:
        return KnowledgePackage(
            source_id=source_id,
            artifacts=tuple(sorted(
                artifacts,
                key=lambda a: (a.kind, a.key))),
            is_authority=False,
        )

    def read(
        self,
        package: KnowledgePackage,
        kinds: Tuple[str, ...] = (),
        keys: Tuple[str, ...] = (),
    ) -> Tuple[KnowledgeArtifact, ...]:
        """Membaca knowledge & memfilter berdasarkan kind/key (read-only)."""
        result = package.artifacts
        if kinds:
            result = tuple(a for a in result if a.kind in kinds)
        if keys:
            result = tuple(a for a in result if a.key in keys)
        return result

    def has_authority(self, package: KnowledgePackage) -> bool:
        """Knowledge exchange tidak pernah membawa otoritas."""
        return package.is_authority
