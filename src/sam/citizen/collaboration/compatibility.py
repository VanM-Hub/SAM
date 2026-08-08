# Compatibility Analyzer - WP-13
# IP-3.3-002 (AO-3.3-001 / ED-3.3-001 2nd cycle)
#
# Memverifikasi kompatibilitas capability & contract antar citizen.
# Kompatibilitas = penilaian kecocokan (matching), BUKAN otorisasi eksekusi.
# Guardrail: Compatibility != Authority.

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class CompatibilityVerdict:
    """Hasil penilaian kompatibilitas (immutable)."""

    compatible: bool
    reasons: Tuple[str, ...] = ()
    matched_contracts: Tuple[str, ...] = ()
    basis: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        return {
            "compatible": self.compatible,
            "reasons": list(self.reasons),
            "matched_contracts": list(self.matched_contracts),
            "basis": list(self.basis),
        }


@dataclass(frozen=True)
class CompatibilityReport:
    """Laporan kompatibilitas antar dua citizen (per capability)."""

    source_identity_id: str
    target_identity_id: str
    entries: Tuple["CapabilityCompatibility", ...] = ()

    @property
    def is_compatible(self) -> bool:
        if not self.entries:
            return False
        return all(e.verdict.compatible for e in self.entries)

    def as_dict(self) -> Dict[str, object]:
        return {
            "source_identity_id": self.source_identity_id,
            "target_identity_id": self.target_identity_id,
            "is_compatible": self.is_compatible,
            "entries": [e.as_dict() for e in self.entries],
        }


@dataclass(frozen=True)
class CapabilityCompatibility:
    """Kompatibilitas satu pasangan capability/contract."""

    contract: str
    source_has: bool
    target_has: bool
    source_schema: str
    target_schema: str
    verdict: CompatibilityVerdict

    def as_dict(self) -> Dict[str, object]:
        return {
            "contract": self.contract,
            "source_has": self.source_has,
            "target_has": self.target_has,
            "source_schema": self.source_schema,
            "target_schema": self.target_schema,
            "verdict": self.verdict.as_dict(),
        }


class CompatibilityAnalyzer:
    """Menilai kompatibilitas capability & contract antar citizen.

    Deterministik: skema yang sama / output yang cocok input -> compatible.
    Hanya PENDAPAT kompatibilitas; tidak men-trigger apapun.
    """

    def compatible(self,
                   source_contracts: Tuple[str, ...],
                   target_contracts: Tuple[str, ...],
                   source_capabilities: Tuple[str, ...] = (),
                   target_capabilities: Tuple[str, ...] = (),
                   schemas: Optional[Dict[str, str]] = None,
                   required_contracts: Tuple[str, ...] = ()) -> CompatibilityVerdict:
        """Periksa apakah source kompatibel dengan target utk contract tertentu.

        `required_contracts`: contract yang HRS didukung target agar compatible.
        Bila kosong, hanya cek overlap contract yang saing mini.
        """
        schemas = schemas or {}
        checks = required_contracts or \
            tuple(sorted(set(source_contracts) & set(target_contracts)))
        matched = []
        reasons = []
        for c in checks:
            src_has = c in source_contracts
            tgt_has = c in target_contracts
            if required_contracts and (not tgt_has):
                reasons.append("target lacks required contract {!r}".format(c))
                continue
            src_schema = schemas.get(c + ":source", "any")
            tgt_schema = schemas.get(c + ":target", "any")
            if src_has and tgt_has:
                matched.append(c)
        if required_contracts and not matched:
            return CompatibilityVerdict(
                compatible=False,
                reasons=tuple(reasons) or ("no required contract matched",),
                basis=("compatibility is assessment, not authority",),
            )
        if not matched:
            return CompatibilityVerdict(
                compatible=False,
                reasons=("no shared contract",),
                basis=("compatibility is assessment, not authority",),
            )
        return CompatibilityVerdict(
            compatible=True,
            reasons=("shared contracts: {!s}".format(", ".join(matched)),),
            matched_contracts=tuple(matched),
            basis=("contract-driven compatibility", "deterministic",
                   "compatibility != authority"),
        )

    def build_report(self, source_identity_id: str, target_identity_id: str,
                     source_contracts: Tuple[str, ...],
                     target_contracts: Tuple[str, ...],
                     source_capabilities: Tuple[str, ...] = (),
                     target_capabilities: Tuple[str, ...] = (),
                     schemas: Optional[Dict[str, str]] = None,
                     required_contracts: Tuple[str, ...] = ()) -> CompatibilityReport:
        """Bangun laporan kompatibilitas penuh."""
        # kontrak yang diperiksa: overlap (default) atau required (eksplisit)
        overlap = sorted(set(source_contracts) & set(target_contracts))
        checks = overlap or list(required_contracts)
        entries = []
        for contract in checks:
            v = self.compatible(
                source_contracts, target_contracts,
                source_capabilities, target_capabilities,
                schemas, required_contracts=(contract,))
            entries.append(CapabilityCompatibility(
                contract=contract,
                source_has=contract in source_contracts,
                target_has=contract in target_contracts,
                source_schema=(schemas or {}).get(contract + ":source", "any"),
                target_schema=(schemas or {}).get(contract + ":target", "any"),
                verdict=v,
            ))
        return CompatibilityReport(source_identity_id, target_identity_id,
                                   tuple(entries))
