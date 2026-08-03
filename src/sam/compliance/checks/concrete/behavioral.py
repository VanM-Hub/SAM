"""L3 behavioral + import-rule checkers (P1-008 Batch 4).

L3 checks verify behavioral invariants of the runtime units:

  * Determinism (L3-D01..D07) — the unit's test module covering
    determinism exists in the baseline test tree.
  * Idempotency (L3-ID01..ID04) — the idempotency behavioral test
    coverage exists.
  * Lifecycle (L3-LC01..LC07) — lifecycle transition test coverage
    exists.
  * Isolation (L3-IS03/IS04) — per-unit boundary/construction tests and
    independent testability.
  * Import rules (L3-IS01/IS02) — IMPORT_ILLEGAL: no runtime unit
    imports another runtime unit, and no runtime unit imports the
    presentation layer.

All coverage targets are resolved from the BaselineSnapshot (test tree),
never hardcoded paths. Source content for import analysis is read via
the shared DiskReader (baseline-, not filesystem-, driven). Output is
deterministic.
"""

from __future__ import annotations

import re

from typing import Dict, List, Optional, Sequence, Tuple

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult
from ._shared import BaselineResolver, DiskReader, SnapshotReader

_RUNTIME_PREFIX = "src/sam/runtime/"
_TEST_PREFIX = "tests/runtime/"

_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+(\S+)\s+import\s+|import\s+(\S+))", re.MULTILINE)


def _discover_units(reader: SnapshotReader) -> List[str]:
    """Runtime unit names, ordered, from the snapshot's source tree.

    A unit is a top-level package under src/sam/runtime/ that carries a
    models/ subpackage (a citizen unit). Deterministic ordering.
    """
    units = []
    for name in reader.dir_names_under(_RUNTIME_PREFIX, depth=1):
        if name.startswith("__"):
            continue
        if reader.exists("%s%s/models" % (_RUNTIME_PREFIX, name)):
            units.append(name)
    return sorted(units)


def _top_module(import_spec: str) -> str:
    """First dotted segment of an import spec: ``a.b.c`` -> ``a``."""
    if not import_spec:
        return ""
    return import_spec.split(".")[0].strip()


def _module_of(path: str) -> str:
    """Convert a source relpath to its dotted module path.

    ``src/sam/runtime/foo/bar.py`` -> ``sam.runtime.foo.bar``.
    Handles __init__ -> package module.
    """
    parts = [p for p in path.split("/") if p]
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


class BehavioralTestCoverageCheck(BaseComplianceCheck):
    """TEST_PASS: unit's behavioral invariant has test coverage.

    Config fields:
        unit: runtime unit name (derived from snapshot in builder).
        required_tests: test-file basenames (e.g. ``test_determinism``)
                        that must exist under tests/runtime/<unit>/.
        unit_requirements: optional mapping unit -> required tests to
                           check many units at once (e.g. L3-IS03 across
                           every unit). Mutually exclusive with unit.
    """

    def __init__(
        self,
        unit: Optional[str] = None,
        required_tests: Sequence[str] = None,
        unit_requirements: Optional[dict] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._unit = unit
        self._required_tests = tuple(required_tests or ())
        # unit -> tuple(required test basenames)
        self._unit_reqs = {
            k: tuple(v) for k, v in (unit_requirements or {}).items()}

    @property
    def unit(self) -> Optional[str]:
        return self._unit

    @property
    def required_tests(self) -> tuple:
        return self._required_tests

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        coverage = {}
        missing_all = {}
        for unit, reqs in self._unit_reqs.items():
            have = set()
            test_dir = "%s%s/" % (_TEST_PREFIX, unit)
            for e in reader.test_files():
                if not e.relative_path.startswith(test_dir):
                    continue
                name = e.relative_path[len(test_dir):]
                if name.endswith(".py"):
                    have.add(name[:-3])
            coverage[unit] = sorted(have)
            miss = [t for t in reqs if t not in have]
            if miss:
                missing_all[unit] = miss

        if not self._unit_reqs:
            # Single-unit mode.
            test_dir = "%s%s/" % (_TEST_PREFIX, self._unit)
            have = set()
            for e in reader.test_files():
                if not e.relative_path.startswith(test_dir):
                    continue
                name = e.relative_path[len(test_dir):]
                if name.endswith(".py"):
                    have.add(name[:-3])
            missing = [t for t in self._required_tests if t not in have]
            if not missing:
                return CheckResult.success(
                    details="Unit '%s' has behavioral test coverage: %s"
                            % (self._unit, ", ".join(self._required_tests)),
                    evidence={
                        "unit": self._unit,
                        "required": list(self._required_tests),
                        "present": sorted(have),
                        "missing": [],
                    },
                )
            return CheckResult.failure(
                details="Unit '%s' missing behavioral test module(s): %s"
                        % (self._unit, ", ".join(missing)),
                evidence={
                    "unit": self._unit,
                    "required": list(self._required_tests),
                    "present": sorted(have),
                    "missing": missing,
                },
            )

        # Multi-unit mode (e.g. L3-IS03 across all units).
        if not missing_all:
            return CheckResult.success(
                details="All %d unit(s) have required isolation coverage"
                        % len(self._unit_reqs),
                evidence={"unit_requirements": self._unit_reqs,
                          "coverage": coverage, "missing": {}},
            )
        return CheckResult.failure(
            details="Isolation coverage lacking in unit(s): %s"
                    % ", ".join(sorted(missing_all)),
            evidence={"unit_requirements": self._unit_reqs,
                      "coverage": coverage, "missing": missing_all},
        )


class ImportIsolationCheck(BaseComplianceCheck):
    """IMPORT_ILLEGAL: runtime units respect import boundaries.

    Derives the unit set from the snapshot, reads each unit's Python
    source via DiskReader, and flags imports that cross the boundary:

      * IS01 (forbid_unit_import=True): a unit importing another unit.
      * IS02 (forbid_unit_import=False, forbid_presentation=True):
        a unit importing the presentation layer.

    Never scans the filesystem — the snapshot names the files.
    """

    def __init__(
        self,
        forbid_unit_import: bool = True,
        forbid_presentation: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._forbid_unit = forbid_unit_import
        self._forbid_pres = forbid_presentation

    def execute(self, context: CheckContext) -> CheckResult:
        snapshot = BaselineResolver().resolve(context)
        reader = SnapshotReader(snapshot)
        root = context.options.get("baseline_root") or context.target_path
        reader_disk = DiskReader(root)

        units = _discover_units(reader)
        violations: List[dict] = []
        for unit in units:
            base = "%s%s/" % (_RUNTIME_PREFIX, unit)
            for e in snapshot.source_files():
                if not e.relative_path.startswith(base):
                    continue
                content = reader_disk.read(e.relative_path)
                importer = _module_of(e.relative_path)
                for m in _IMPORT_RE.finditer(content):
                    spec = m.group(1) or m.group(2)
                    target = _top_module(spec)
                    if target == "sam" and "." in spec:
                        full = spec
                        # sam.runtime.<other-unit> or sam.presentation.*
                        parts = full.split(".")
                        if self._forbid_unit and len(parts) >= 3 \
                                and parts[1] == "runtime" \
                                and parts[2] in units and parts[2] != unit:
                            violations.append({
                                "file": e.relative_path,
                                "importer": importer,
                                "import": full,
                                "rule": "cross-unit",
                            })
                        if self._forbid_pres and len(parts) >= 2 \
                                and parts[1] == "presentation":
                            violations.append({
                                "file": e.relative_path,
                                "importer": importer,
                                "import": full,
                                "rule": "presentation",
                            })

        if not violations:
            rule = ("cross-unit" if self._forbid_unit
                    else "presentation-import")
            return CheckResult.success(
                details="No %s import violations across %d unit(s): %s"
                        % (rule, len(units), ", ".join(units)),
                evidence={
                    "rule": rule,
                    "units": units,
                    "violations": [],
                },
            )
        return CheckResult.failure(
            details="%d import-boundary violation(s) found"
                    % len(violations),
            evidence={
                "rule": ("cross-unit" if self._forbid_unit
                         else "presentation-import"),
                "units": units,
                "violations": violations,
                "violation_count": len(violations),
            },
        )


class IndependentTestabilityCheck(BaseComplianceCheck):
    """IS04: each unit is independently testable.

    Verifies every discovered runtime unit has a corresponding test
    directory with at least one construction/health test module, so it
    can be tested in isolation. Test presence derived from the snapshot.
    """

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        units = _discover_units(reader)
        unmet = []
        coverage = {}
        for unit in units:
            test_dir = "%s%s/" % (_TEST_PREFIX, unit)
            names = [e.relative_path for e in reader.test_files()
                     if e.relative_path.startswith(test_dir)]
            coverage[unit] = names
            # A unit is independently testable when it has a dedicated
            # test package containing at least one real test module.
            real_tests = [n for n in names if n.endswith(".py")
                          and not n.endswith("__init__.py")]
            if not real_tests:
                unmet.append(unit)
        if not unmet:
            return CheckResult.success(
                details="All %d unit(s) independently testable"
                        % len(units),
                evidence={"units": units, "coverage": coverage,
                          "unmet": []},
            )
        return CheckResult.failure(
            details="Unit(s) lacking independent tests: %s"
                    % ", ".join(unmet),
            evidence={"units": units, "coverage": coverage, "unmet": unmet},
        )
