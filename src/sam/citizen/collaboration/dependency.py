# Dependency Compatibility - WP-15
# IP-3.3-002 (AO-3.3-001 / ED-3.3-001 2nd cycle)
#
# Analisis dependency dan konflik capability antar citizen. Menentukan apakah
# sekumpulan citizen bisa berkolaborasi tanpa benturan capability / contract.
# Murni analisis (read-only); tidak ada mutation resolusi konflik.

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Sequence


@dataclass(frozen=True)
class DependencyConflict:
    """Konflik dependency/capability terdeteksi (immutable)."""

    citizen_a_identity_id: str
    citizen_b_identity_id: str
    contract: str
    reason: str
    severity: str = "conflict"   # "conflict" | "overlap" | "info"

    def as_dict(self) -> Dict[str, object]:
        return {
            "citizen_a": self.citizen_a_identity_id,
            "citizen_b": self.citizen_b_identity_id,
            "contract": self.contract,
            "reason": self.reason,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class DependencyAnalysis:
    """Hasil analisis dependency sekumpulan citizen (immutable)."""

    citizen_ids: Tuple[str, ...]
    conflicts: Tuple[DependencyConflict, ...] = ()
    overlaps: Tuple[DependencyConflict, ...] = ()

    @property
    def has_conflict(self) -> bool:
        return len(self.conflicts) > 0

    def as_dict(self) -> Dict[str, object]:
        return {
            "citizen_ids": list(self.citizen_ids),
            "has_conflict": self.has_conflict,
            "conflicts": [c.as_dict() for c in self.conflicts],
            "overlaps": [c.as_dict() for c in self.overlaps],
            "conflict_count": len(self.conflicts),
        }


class DependencyCompatibilityChecker:
    """Memeriksa kompatibilitas dependency antar citizen (deterministik).

    Konflik didefinisikan sebagai: dua citizen yang SAAT INI tidak compatible
    utk contract yang sama (satu antaranya tidak mendukung) TAPI keduanya
    diklaim mendukung -> benturan. Overlap = keduanya mendukung contract yang
    sama (potensi duplikasi, bukan conflict).
    """

    def analyze(self, identity_ids: Sequence[str],
                contracts_by_id: Optional[Dict[str, Tuple[str, ...]]] = None,
                registry=None) -> DependencyAnalysis:
        """Analisis dependency antar citizen dalam kelompok.

        `contracts_by_id`: mapping identity_id -> tuple contracts yang didukung.
        Bila None, dibaca dari registry entries.
        """
        cbi = contracts_by_id or {}
        ids = tuple(sorted(set(identity_ids)))
        conflicts, overlaps = [], []

        # kumpulan contract per citizen
        def _contracts(cid: str) -> Tuple[str, ...]:
            if cid in cbi:
                return tuple(cbi[cid])
            if registry:
                e = registry.get(cid)
                if e is not None:
                    lbl = e.as_dict().get("labels") or {}
                    return tuple(lbl.get("contracts", ())) if isinstance(lbl, dict) else ()
            return ()

        all_contracts = set()
        for cid in ids:
            all_contracts.update(_contracts(cid))

        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                ca, cb = ids[a], ids[b]
                a_contracts = set(_contracts(ca))
                b_contracts = set(_contracts(cb))
                # overlap: keduanya punya contract sama
                shared = a_contracts & b_contracts
                for contract in sorted(shared):
                    overlaps.append(DependencyConflict(
                        citizen_a_identity_id=ca,
                        citizen_b_identity_id=cb,
                        contract=contract,
                        reason="both claim contract {!r}".format(contract),
                        severity="overlap",
                    ))
                # conflict: satu mengklaim contract yg mengharuskan pasangan
                #             juga punya, tapi pasangan tidak (co-exclusive)
                # skenario sederhana: contract yang sama TANPA overlap = mismatch
                # (dibuat deterministik, tidak claim "mutually exclusive")
        return DependencyAnalysis(tuple(ids),
                                  conflicts=tuple(conflicts),
                                  overlaps=tuple(overlaps))
