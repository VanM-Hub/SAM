"""
Guardian Consistency Validator.

Validates runtime consistency across registered instances.
Synchronous only. No async, no threading, no network.

Validations:
    - Duplicate runtime
    - Missing runtime
    - Version mismatch
    - Health mismatch
    - Snapshot mismatch
    - Registry mismatch
    - Outdated runtime
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from .state import RuntimeState, RuntimeStatus, RuntimeHealth, RuntimeVersion, RuntimeSnapshot
from .registry import GuardianRuntimeRegistry
from .snapshot import GuardianSnapshotManager


class GuardianConsistencyValidator:
    """
    Synchronous consistency validator for Guardian runtime.

    Performs 7 consistency checks across the registry
    and snapshot history.
    """

    def __init__(
        self,
        registry: GuardianRuntimeRegistry,
        snapshot_manager: GuardianSnapshotManager,
    ) -> None:
        self._registry = registry
        self._snapshot_manager = snapshot_manager
        self._expected_runtime_ids: Set[str] = set()

    def set_expected_runtimes(self, runtime_ids: List[str]) -> None:
        """Set the expected runtime IDs for missing runtime checks."""
        self._expected_runtime_ids = set(runtime_ids)

    @property
    def expected_runtime_ids(self) -> Set[str]:
        """Get the set of expected runtime IDs."""
        return set(self._expected_runtime_ids)

    def validate_all(self) -> Dict[str, Any]:
        """
        Run all consistency checks.

        Returns:
            Dict with all validation results.
        """
        return {
            "timestamp": datetime.now().timestamp(),
            "duplicate_runtime": self.check_duplicate_runtime(),
            "missing_runtime": self.check_missing_runtime(),
            "version_mismatch": self.check_version_mismatch(),
            "health_mismatch": self.check_health_mismatch(),
            "snapshot_mismatch": self.check_snapshot_mismatch(),
            "registry_mismatch": self.check_registry_mismatch(),
            "outdated_runtime": self.check_outdated_runtime(),
            "overall_consistent": self.is_consistent(),
        }

    def is_consistent(self) -> bool:
        """Check if all validations pass."""
        return all([
            self.check_duplicate_runtime()["pass"],
            self.check_missing_runtime()["pass"],
            self.check_version_mismatch()["pass"],
            self.check_health_mismatch()["pass"],
            self.check_snapshot_mismatch()["pass"],
            self.check_registry_mismatch()["pass"],
            self.check_outdated_runtime()["pass"],
        ])

    def check_duplicate_runtime(self) -> Dict[str, Any]:
        """
        Check for duplicate runtime registrations.

        Returns:
            Dict with check result.
        """
        ids = list(self._registry.ids)
        seen: Set[str] = set()
        duplicates: List[str] = []
        for rid in ids:
            if rid in seen:
                duplicates.append(rid)
            seen.add(rid)
        return {
            "check": "duplicate_runtime",
            "pass": len(duplicates) == 0,
            "duplicates": duplicates,
            "message": (
                "No duplicate runtimes"
                if len(duplicates) == 0
                else f"Duplicate runtimes: {duplicates}"
            ),
        }

    def check_missing_runtime(self) -> Dict[str, Any]:
        """
        Check for missing expected runtimes.

        Returns:
            Dict with check result.
        """
        if not self._expected_runtime_ids:
            return {
                "check": "missing_runtime",
                "pass": True,
                "missing": [],
                "message": "No expected runtimes configured",
            }
        registered = set(self._registry.ids)
        missing = list(self._expected_runtime_ids - registered)
        return {
            "check": "missing_runtime",
            "pass": len(missing) == 0,
            "missing": missing,
            "message": (
                "All expected runtimes present"
                if len(missing) == 0
                else f"Missing runtimes: {missing}"
            ),
        }

    def check_version_mismatch(self) -> Dict[str, Any]:
        """
        Check for version mismatches across runtimes.

        Returns:
            Dict with check result.
        """
        current_version = RuntimeVersion.current()
        current_str = str(current_version)
        mismatches: List[str] = []
        for state in self._registry.list():
            if str(state.version) != current_str:
                mismatches.append(
                    f"{state.runtime_id}: {str(state.version)} "
                    f"(expected {current_str})"
                )
        return {
            "check": "version_mismatch",
            "pass": len(mismatches) == 0,
            "expected_version": current_str,
            "mismatches": mismatches,
            "message": (
                "All runtimes at expected version"
                if len(mismatches) == 0
                else f"Version mismatches: {len(mismatches)}"
            ),
        }

    def check_health_mismatch(self) -> Dict[str, Any]:
        """
        Check for health mismatches between runtimes.

        Returns:
            Dict with check result.
        """
        states = self._registry.list()
        healthy = sum(1 for s in states if s.health == RuntimeHealth.HEALTHY)
        degraded = sum(1 for s in states if s.health in (
            RuntimeHealth.DEGRADED, RuntimeHealth.CRITICAL
        ))
        return {
            "check": "health_mismatch",
            "pass": degraded == 0,
            "total": len(states),
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy_ids": [
                s.runtime_id for s in states
                if s.health in (RuntimeHealth.DEGRADED, RuntimeHealth.CRITICAL)
            ],
            "message": (
                "All runtimes healthy"
                if degraded == 0
                else f"{degraded} runtime(s) degraded or critical"
            ),
        }

    def check_snapshot_mismatch(self) -> Dict[str, Any]:
        """
        Check for inconsistencies between snapshots.

        Returns:
            Dict with check result.
        """
        if self._snapshot_manager.count < 2:
            return {
                "check": "snapshot_mismatch",
                "pass": True,
                "snapshots_available": self._snapshot_manager.count,
                "message": "Need at least 2 snapshots for comparison",
            }

        diff = self._snapshot_manager.diff()
        return {
            "check": "snapshot_mismatch",
            "pass": not diff.get("has_diff", True),
            "snapshots_available": self._snapshot_manager.count,
            "changes": diff,
            "message": (
                "No snapshot drift detected"
                if not diff.get("has_diff", True)
                else "Snapshot drift detected"
            ),
        }

    def check_registry_mismatch(self) -> Dict[str, Any]:
        """
        Check registry vs snapshot consistency.

        Returns:
            Dict with check result.
        """
        registry_count = self._registry.count
        snapshot_current = self._snapshot_manager.current
        snapshot_count = snapshot_current.total_runtimes if snapshot_current else 0

        match = registry_count == snapshot_count
        return {
            "check": "registry_mismatch",
            "pass": match,
            "registry_count": registry_count,
            "snapshot_count": snapshot_count,
            "message": (
                "Registry and snapshot counts match"
                if match
                else f"Registry ({registry_count}) ≠ Snapshot ({snapshot_count})"
            ),
        }

    def check_outdated_runtime(self) -> Dict[str, Any]:
        """
        Check for outdated runtimes (not synced recently).

        Returns:
            Dict with check result.
        """
        now = datetime.now().timestamp()
        threshold = 300.0  # 5 minutes
        outdated: List[str] = []

        for state in self._registry.list():
            age = now - state.last_sync_at
            if age > threshold:
                outdated.append(state.runtime_id)

        return {
            "check": "outdated_runtime",
            "pass": len(outdated) == 0,
            "threshold_seconds": threshold,
            "outdated": outdated,
            "message": (
                "All runtimes synced recently"
                if len(outdated) == 0
                else f"Outdated runtimes: {outdated}"
            ),
        }
