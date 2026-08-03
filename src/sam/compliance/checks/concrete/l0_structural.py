"""L0 Structural checkers (P1-008 Batch 1).

The 12 L0 checks verify the physical structure of the Runtime package
against I1-001 / I0-001. Their unit inventory is derived from the
BaselineSnapshot, never hardcoded: a "runtime unit" is any directory
under the runtime package that exposes the canonical skeleton
(models/, interfaces/, services/, lifecycle/, validation/, exceptions/).

Checkers read the snapshot via BaselineResolver and never scan the
filesystem themselves.

Python 3.8 compatible.
"""

from __future__ import annotations

from typing import List, Optional

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult
from ._shared import BaselineResolver, SnapshotReader

# Canonical skeleton sub-directories every runtime unit must expose.
_CORE_SKELETON = ("models", "interfaces", "services", "lifecycle",
                  "validation", "exceptions")
# Sub-directories added when a unit holds state/enums.
_STATE_DIR = "state"

# Namespace for the runtime package (derived from authority, not a list of
# unit names — the units themselves are discovered from the baseline).
_RUNTIME_PREFIX = "src/sam/runtime/"


def _discover_units(reader: SnapshotReader) -> List[str]:
    """Derive runtime unit directory names from the baseline snapshot.

    A unit is a directory directly under the runtime package that
    exposes the canonical skeleton. The defining marker is a `models/`
    sub-package (every runtime unit declares models; support dirs like
    contracts/internal/registry/shared do not). Units are discovered,
    never hardcoded.
    """
    units = []
    for child in reader.dir_children(_RUNTIME_PREFIX):
        if child.startswith("__"):
            continue
        if _unit_has_dir(reader, child, "models"):
            units.append(child)
    return units


def _unit_has_dir(reader: SnapshotReader, unit: str, sub: str) -> bool:
    path = "%s%s/%s" % (_RUNTIME_PREFIX, unit, sub)
    return reader.exists(path)


def _unit_has_state_model(reader: SnapshotReader, unit: str) -> bool:
    """Whether a unit has state/enum bearing model files indexed."""
    base = "%s%s/" % (_RUNTIME_PREFIX, unit)
    for e in reader.files_under(base):
        name = e.relative_path.rsplit("/", 1)[-1].lower()
        rel = e.relative_path[len(base):]
        if "state" in name or "enum" in name:
            return True
        if rel.startswith("state/") or rel.startswith("enums/"):
            return True
    return False


class RuntimeUnitCountCheck(BaseComplianceCheck):
    """L0-01/L0-02: exactly 7 runtime units exist (no 8th).

    Unit inventory derived from the snapshot. L0-01 passes when at
    least 7 units exist; L0-02 (absent-type) passes only when exactly
    7 exist (no 8th unit).
    """

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        units = [u for u in _discover_units(reader) if not u.startswith("__")]
        count = len(units)
        if self.check_id == "L0-02":
            # Absent-type: no 8th unit -> exactly 7.
            if count == 7:
                return CheckResult.success(
                    details="Exactly %d runtime units (no 8th): %s"
                            % (count, ", ".join(sorted(units))),
                    evidence={"unit_count": count, "units": sorted(units)},
                )
            return CheckResult.failure(
                details="Expected 7 runtime units, found %d: %s"
                        % (count, ", ".join(sorted(units))),
                evidence={"unit_count": count, "units": sorted(units)},
            )
        if count >= 7:
            return CheckResult.success(
                details="%d runtime units present (expected >= 7): %s"
                        % (count, ", ".join(sorted(units))),
                evidence={"unit_count": count, "units": sorted(units)},
            )
        return CheckResult.failure(
            details="Expected >= 7 runtime units, found %d: %s"
                    % (count, ", ".join(sorted(units))),
            evidence={"unit_count": count, "units": sorted(units)},
        )


class RuntimeUnitSkeletonCheck(BaseComplianceCheck):
    """L0-03..L0-08: each unit exposes a required skeleton sub-directory.

    For a given sub-directory (models/interfaces/services/lifecycle/
    validation/exceptions), every derived unit must have it. The
    required sub is supplied via the check configuration.
    """

    def __init__(self, sub: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._sub = sub

    @property
    def sub(self) -> str:
        return self._sub

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        units = [u for u in _discover_units(reader) if not u.startswith("__")]
        missing = [u for u in units if not _unit_has_dir(reader, u, self._sub)]
        if not missing:
            return CheckResult.success(
                details="All %d units expose %s/ subdirectory"
                        % (len(units), self._sub),
                evidence={"sub": self._sub, "units": sorted(units),
                          "missing": []},
            )
        return CheckResult.failure(
            details="Units missing %s/: %s" % (self._sub, ", ".join(sorted(missing))),
            evidence={"sub": self._sub, "units": sorted(units),
                      "missing": sorted(missing)},
        )


class RuntimeInitPresenceCheck(BaseComplianceCheck):
    """L0-10: all expected __init__.py files present.

    Scans the derived unit skeleton (unit, and each required sub-dir)
    and verifies each has an __init__.py indexed in the baseline.
    """

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        units = [u for u in _discover_units(reader) if not u.startswith("__")]
        missing = []
        for unit in units:
            for sub in _CORE_SKELETON + (_STATE_DIR,):
                if _unit_has_dir(reader, unit, sub):
                    pkg = "%s%s/%s" % (_RUNTIME_PREFIX, unit, sub)
                    if not reader.exists(pkg.rstrip("/") + "/__init__.py"):
                        missing.append(pkg + "/__init__.py")
            if not reader.exists("%s%s/__init__.py"
                                 % (_RUNTIME_PREFIX, unit)):
                missing.append("%s%s/__init__.py" % (_RUNTIME_PREFIX, unit))
        if not missing:
            return CheckResult.success(
                details="All %d units + sub-packages have __init__.py"
                        % len(units),
                evidence={"missing": [], "units": sorted(units)},
            )
        return CheckResult.failure(
            details="Missing __init__.py: %s" % ", ".join(sorted(missing)),
            evidence={"missing": sorted(missing), "units": sorted(units)},
        )


class RuntimeNoExtraTopLevelCheck(BaseComplianceCheck):
    """L0-11: no extra top-level directories in the runtime package.

    Only directories are considered (files are legitimate runtime
    modules). Allowed directories: derived units + known support
    namespaces (contracts, internal, registry, shared). __pycache__ is
    build noise and ignored.
    """

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        units = set(_discover_units(reader))
        support = {"contracts", "internal", "registry", "shared"}
        dirs = reader.dir_names_under(_RUNTIME_PREFIX, depth=1)
        extras = sorted(
            d for d in dirs
            if d not in units and d not in support and not d.startswith("__")
        )
        if not extras:
            return CheckResult.success(
                details="No extra top-level dirs in runtime: %s"
                        % ", ".join(sorted(dirs)),
                evidence={"dirs": sorted(dirs), "extras": []},
            )
        return CheckResult.failure(
            details="Unexpected top-level dirs: %s" % ", ".join(extras),
            evidence={"dirs": sorted(dirs), "extras": extras},
        )


class RuntimeUnitStateCheck(BaseComplianceCheck):
    """L0-09: units with state/enums expose a state/ subdirectory.

    A unit "has state" when the baseline indexes a state/ package or a
    state/enum-bearing model file under it. Units without state content
    (e.g. citizen_host) are not required to have state/.
    """

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        units = [u for u in _discover_units(reader) if not u.startswith("__")]
        problems = []
        for unit in units:
            unit_base = "%s%s" % (_RUNTIME_PREFIX, unit)
            has_state_pkg = reader.exists(unit_base + "/state")
            has_state_model = _unit_has_state_model(reader, unit)
            if (has_state_pkg or has_state_model) and not has_state_pkg:
                problems.append(unit)
        if not problems:
            return CheckResult.success(
                details="All units with state content expose state/ "
                        "(%d units scanned)" % len(units),
                evidence={"units": sorted(units), "missing": []},
            )
        return CheckResult.failure(
            details="Units with state but no state/: %s"
                    % ", ".join(sorted(problems)),
            evidence={"units": sorted(units), "missing": sorted(problems)},
        )


class TestMirrorCheck(BaseComplianceCheck):
    """L0-12: test directory mirrors source structure.

    For every derived unit in the runtime package there must be a
    corresponding test directory under the test tree.
    """

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        units = [u for u in _discover_units(reader) if not u.startswith("__")]
        missing = []
        for unit in units:
            test_dir = "tests/runtime/%s/" % unit
            if not reader.files_under(test_dir):
                # Also try tests/{unit}/ mirror location.
                if not reader.files_under("tests/%s/" % unit):
                    missing.append(unit)
        if not missing:
            return CheckResult.success(
                details="All %d units mirrored in test tree"
                        % len(units),
                evidence={"units": sorted(units), "missing": []},
            )
        return CheckResult.failure(
            details="Units without test mirror: %s"
                    % ", ".join(sorted(missing)),
            evidence={"units": sorted(units), "missing": sorted(missing)},
        )
