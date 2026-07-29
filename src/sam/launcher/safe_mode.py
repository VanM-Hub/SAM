"""
OP-367 — Safe Mode
===================

Safe mode modifies startup behavior only.
It does NOT change runtime behavior.
"""

import enum
from typing import Optional


class SafeMode(enum.Enum):
    NORMAL = "NORMAL"
    SAFE = "SAFE"
    RECOVERY = "RECOVERY"
    READ_ONLY = "READ_ONLY"
    MINIMAL = "MINIMAL"


class SafeModeManager:
    """Manages safe mode selection.

    Safe mode only influences *startup* — which subsystems are
    initialized and which checks are performed.
    """

    def __init__(self, mode: Optional[str] = None) -> None:
        self._mode = self._resolve(mode or "NORMAL")

    @property
    def mode(self) -> SafeMode:
        return self._mode

    def _resolve(self, mode_str: str) -> SafeMode:
        upper = mode_str.strip().upper()
        for sm in SafeMode:
            if sm.value == upper:
                return sm
        return SafeMode.NORMAL

    @property
    def is_normal(self) -> bool:
        return self._mode == SafeMode.NORMAL

    @property
    def is_safe(self) -> bool:
        return self._mode == SafeMode.SAFE

    @property
    def is_recovery(self) -> bool:
        return self._mode == SafeMode.RECOVERY

    @property
    def is_read_only(self) -> bool:
        return self._mode == SafeMode.READ_ONLY

    @property
    def is_minimal(self) -> bool:
        return self._mode == SafeMode.MINIMAL

    @property
    def skip_diagnostics(self) -> bool:
        """Whether to skip diagnostics on startup."""
        return self._mode in (SafeMode.MINIMAL, SafeMode.RECOVERY)

    @property
    def skip_environment_validation(self) -> bool:
        """Whether to skip environment validation."""
        return self._mode == SafeMode.MINIMAL

    @property
    def skip_plugin_discovery(self) -> bool:
        """Whether to skip plugin discovery."""
        return self._mode in (SafeMode.MINIMAL, SafeMode.SAFE)

    @property
    def readonly_filesystem(self) -> bool:
        """Whether the launcher should avoid filesystem writes."""
        return self._mode in (SafeMode.READ_ONLY, SafeMode.MINIMAL)

    @property
    def label(self) -> str:
        labels = {
            SafeMode.NORMAL: "Normal operation — full startup",
            SafeMode.SAFE: "Safe — plugin discovery skipped",
            SafeMode.RECOVERY: "Recovery — diagnostics skipped",
            SafeMode.READ_ONLY: "Read-only — no filesystem writes",
            SafeMode.MINIMAL: "Minimal — env + diag + plugin skipped",
        }
        return labels.get(self._mode, "Unknown")

    def __repr__(self) -> str:
        return f"<SafeModeManager mode={self._mode.value}>"
