"""M14-004 ScopedAutonomy — autonomy terbatas per Ward/tindakan.

Prinsip M14: authority TIDAK pernah menaik sendiri. ScopedAutonomy menjaga
batas atas otonomi per (ward, capability) yang ditetapkan OWNER lewat grant.
SAM boleh MENURUNKAN level (safety), TIDAK PERNAH menaikkan di atas grant.

Ini memakai ulang AutonomyLevel + AutonomyController, tapi MEMBATASI
adjust_level: kenaikan dilarang (guard); penurunan (degradation) diizinkan
dan dicatat.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sam.autonomy.models import AutonomyLevel


class ScopedAutonomy:
    """Menjaga batas atas otonomi per (ward, capability)."""

    def __init__(self) -> None:
        #  ward_id -> {capability: AutonomyLevel}  (level SAAT INI, <= grant)
        self._current: Dict[str, Dict[str, AutonomyLevel]] = {}
        self._grant_upper: Dict[str, Dict[str, AutonomyLevel]] = {}
        self._history: list = []

    # --- setup (dari owner grant) ---

    def bind(
        self, ward_id: str, capability: str, upper: AutonomyLevel
    ) -> None:
        """Pasang batas atas otonomi (dari grant owner). Tidak pernah > upper.

        Level saat ini dimulai = upper (boleh penuh), tapi SAM hanya bisa
        menurunkannya, tidak menaikkan.
        """
        cap = capability.strip().lower()
        self._grant_upper.setdefault(ward_id, {})[cap] = upper
        # inisialisasi level saat ini bila belum ada (tidak melebihi upper)
        self._current.setdefault(ward_id, {})[cap] = upper

    # --- query ---

    def upper(self, ward_id: str, capability: str) -> Optional[AutonomyLevel]:
        return self._grant_upper.get(ward_id, {}).get(capability.strip().lower())

    def current(self, ward_id: str, capability: str) -> Optional[AutonomyLevel]:
        return self._current.get(ward_id, {}).get(capability.strip().lower())

    def grant_allows(
        self, ward_id: str, capability: str, level: AutonomyLevel, risk: str = "low"
    ) -> bool:
        """Apakah grant upper mengizinkan level ini untuk capability tsb?"""
        upper = self.upper(ward_id, capability)
        if upper is None:
            return False
        # fail-closed: level yang diminta tidak boleh melebihi upper numeric.
        # kenaikan dari current TIDAK diizinkan (self-grant dilarang) - hanya
        # eksekusi dengan  level <= upper yang valid.
        return level.numeric <= upper.numeric and upper.can_execute(risk)

    # --- penurunan (degradation) ---

    def degrade(
        self, ward_id: str, capability: str, reason: str = ""
    ) -> Optional[AutonomyLevel]:
        """Turunkan level saat ini satu tingkat (safety). TIDAK menaikkan.

        Returns level baru (atau None bila tidak ada binding). Dicatat ke history.
        """
        cap = capability.strip().lower()
        current = self.current(ward_id, cap)
        if current is None:
            return None
        new_numeric = max(1, current.numeric - 1)
        new_level = AutonomyLevel.from_numeric(new_numeric)
        self._current[ward_id][cap] = new_level
        self._history.append({
            "ward_id": ward_id,
            "capability": cap,
            "from": current.value,
            "to": new_level.value,
            "reason": reason,
        })
        return new_level

    # --- history / audit ---

    def history(self, limit: int = 100) -> list:
        h = list(self._history)
        h.reverse()
        return h[:limit]

    def snapshot(self, ward_id: str) -> Dict[str, Any]:
        cur = self._current.get(ward_id, {})
        upper = self._grant_upper.get(ward_id, {})
        return {
            "ward_id": ward_id,
            "current": {k: v.value for k, v in cur.items()},
            "upper_bound": {k: v.value for k, v in upper.items()},
        }
