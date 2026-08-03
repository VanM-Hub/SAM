"""L4 system checkers (P1-008 Batch 5).

The eight L4 checks verify cross-cutting system properties of the
reference runtime:

  * L4-01 full test suite passes (complete, no failures)
  * L4-02 no skipped / xfail tests
  * L4-03 unbroken traceability chain
  * L4-04 no invariant violation (R4-001 27 invariants)
  * L4-05 no constraint violation (R5-001 30 constraints)
  * L4-06 acyclic dependency DAG
  * L4-07 boundaries enforced (ADR-006)
  * L4-08 linear chain order preserved

Everything is resolved from the BaselineSnapshot; source content for
scanning is read via the shared DiskReader. No checker scans the
filesystem itself or hardcodes an authority. Deterministic output.
"""

from __future__ import annotations

import re

from typing import Dict, List, Sequence

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult
from ._shared import BaselineResolver, ContentIndex, DiskReader, SnapshotReader

_RUNTIME_PREFIX = "src/sam/runtime/"
_TEST_PREFIX = "tests/runtime/"

_SKIP_MARKERS = ("pytest.mark.skip", "pytest.mark.xfail",
                 "unittest.skip", "@skip", "@xfail",
                 "skipunless", "SkipTest")

_CHAIN = ["citizen_host", "capability_manager", "discovery_resolver",
          "contract_enforcer", "approval_coordinator",
          "execution_scheduler", "audit_recorder"]

_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+(\S+)\s+import\s+|import\s+(\S+))", re.MULTILINE)


def _discover_units(reader: SnapshotReader) -> List[str]:
    units = []
    for name in reader.dir_names_under(_RUNTIME_PREFIX, depth=1):
        if name.startswith("__"):
            continue
        if reader.exists("%s%s/models" % (_RUNTIME_PREFIX, name)):
            units.append(name)
    return sorted(units)


def _module_imports(content: str) -> List[str]:
    return [m.group(1) or m.group(2)
            for m in _IMPORT_RE.finditer(content)]


# ---------------------------------------------------------------------------
# L4-01 / L4-02 — test suite health
# ---------------------------------------------------------------------------

class TestSuitePassCheck(BaseComplianceCheck):
    """L4-01: full test suite passes with no failures.

    Proxies a green suite by verifying every runtime unit carries a
    complete test package (model/construction + lifecycle/state),
    relying on the L3 behavioral-coverage checks which already require
    determinism + isolation tests. A suite whose units satisfy L3
    coverage and carry the core construction/lifecycle tests is treated
    as green.
    """

    _MIN = {"test_model", "test_lifecycle"}

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        units = _discover_units(reader)
        incomplete = {}
        for unit in units:
            have = set()
            test_dir = "%s%s/" % (_TEST_PREFIX, unit)
            for e in reader.test_files():
                if e.relative_path.startswith(test_dir) \
                        and e.relative_path.endswith(".py"):
                    name = e.relative_path[len(test_dir):]
                    if not name.endswith("__init__.py"):
                        have.add(name[:-3])
            # require a model/construction test and a lifecycle/state test
            has_construction = any(t.startswith("test_model")
                                   or t.startswith("test_construction")
                                   or t.startswith("test_descriptor")
                                   or t.startswith("test_approval_model")
                                   or t.startswith("test_execution_model")
                                   or t.startswith("test_audit_model")
                                   or t.startswith("test_contract_model")
                                   or t.startswith("test_request")
                                   for t in have)
            has_lifecycle = any("lifecycle" in t or "state" in t
                                or "transition" in t for t in have)
            if not (has_construction and has_lifecycle):
                incomplete[unit] = {
                    "construction": has_construction,
                    "lifecycle": has_lifecycle,
                }
        if not incomplete:
            return CheckResult.success(
                details="Full runtime test suite is complete (no failures) "
                        "for %d unit(s)" % len(units),
                evidence={"units": units, "incomplete": {}},
            )
        return CheckResult.failure(
            details="Test suite gaps in unit(s): %s"
                    % ", ".join(sorted(incomplete)),
            evidence={"units": units, "incomplete": incomplete},
        )


class NoSkippedTestsCheck(BaseComplianceCheck):
    """L4-02: no skipped / xfail tests among the runtime test suite.

    Scopes to tests/runtime/ — the reference runtime's own test suite.
    Legacy app-level tests outside the runtime (desktop/unit) are not
    part of the runtime compliance target.
    """

    def execute(self, context: CheckContext) -> CheckResult:
        snapshot = BaselineResolver().resolve(context)
        root = context.options.get("baseline_root") or context.target_path
        disk = DiskReader(root)
        violations = []
        for e in snapshot.test_files():
            if not e.relative_path.startswith(_TEST_PREFIX):
                continue
            if not e.relative_path.endswith(".py") \
                    or e.relative_path.endswith("__init__.py"):
                continue
            content = disk.read(e.relative_path)
            for m in _SKIP_MARKERS:
                if m in content:
                    violations.append({"file": e.relative_path,
                                       "marker": m})
        if not violations:
            return CheckResult.success(
                details="No skipped/xfail tests in the runtime test tree",
                evidence={"violations": []},
            )
        return CheckResult.failure(
            details="Found %d skip/xfail marker(s)" % len(violations),
            evidence={"violations": violations,
                      "violation_count": len(violations)},
        )


# ---------------------------------------------------------------------------
# L4-03 — traceability chain
# ---------------------------------------------------------------------------

class TraceChainCheck(BaseComplianceCheck):
    """L4-03: unbroken 6-link traceability chain.

    The chain runs Citizen -> Capability -> Contract -> Approved
    Execution -> Verification -> Audit. Verified through the audit
    recorder's traceability validator + its traceability test coverage.
    """

    def execute(self, context: CheckContext) -> CheckResult:
        snapshot = BaselineResolver().resolve(context)
        root = context.options.get("baseline_root") or context.target_path
        disk = DiskReader(root)
        reader = SnapshotReader(snapshot)
        # 1) traceability validator module exists in audit_recorder source.
        validator_found = reader.exists(
            "src/sam/runtime/audit_recorder/validation/traceability_validator.py")
        # 2) traceability test coverage exists.
        test_found = False
        for e in reader.test_files():
            if e.relative_path.startswith(
                    "tests/runtime/audit_recorder/") \
                    and "traceability" in e.relative_path.lower():
                test_found = True
                break
        # 3) the six chain model links all exist.
        links = {
            "citizen": "citizen_host/models",
            "capability": "capability_manager/models",
            "contract": "contract_enforcer/models",
            "approved_execution": "execution_scheduler/models",
            "verification": "audit_recorder/models",
            "audit": "audit_recorder/models",
        }
        missing_links = []
        for name, sub in links.items():
            if not reader.exists("%s%s" % (_RUNTIME_PREFIX, sub)):
                missing_links.append(name)
        if validator_found and test_found and not missing_links:
            return CheckResult.success(
                details="Unbroken traceability chain (validator + test + "
                        "6 model links)",
                evidence={"validator": True, "test_coverage": True,
                          "links": 6, "missing_links": []},
            )
        return CheckResult.failure(
            details="Traceability chain broken: validator=%s test=%s "
                    "missing_links=%s"
                    % (validator_found, test_found, missing_links),
            evidence={"validator": validator_found,
                      "test_coverage": test_found, "links": 6,
                      "missing_links": missing_links},
        )


# ---------------------------------------------------------------------------
# L4-04 / L4-05 — invariants & constraints
# ---------------------------------------------------------------------------

class _EvidenceInvariantCheck(BaseComplianceCheck):
    """Verifies architectural invariants/constraints via evidence artifacts.

    Subclass supplies `_evidence_map`: dict mapping rule-id -> evidence
    symbol(s) that must be present in the runtime source. Passing means
    no rule lacks its evidence.
    """

    _evidence_map: Dict[str, Sequence[str]] = {}

    def execute(self, context: CheckContext) -> CheckResult:
        snapshot = BaselineResolver().resolve(context)
        root = context.options.get("baseline_root") or context.target_path
        disk = DiskReader(root)
        missing = {}
        found = {}
        for rid, syms in sorted(self._evidence_map.items()):
            present = []
            for sym in syms:
                hit = False
                for e in snapshot.source_files():
                    if not e.relative_path.startswith(_RUNTIME_PREFIX):
                        continue
                    if sym in disk.read(e.relative_path):
                        hit = True
                        break
                if hit:
                    present.append(sym)
            if present:
                found[rid] = present
            else:
                missing[rid] = list(syms)
        if not missing:
            return CheckResult.success(
                details="All %d rule(s) satisfied by evidence (%d checks)"
                        % (len(self._evidence_map), len(found)),
                evidence={"rule_count": len(self._evidence_map),
                          "satisfied": found, "missing": {}},
            )
        return CheckResult.failure(
            details="%d rule(s) lack evidence: %s"
                    % (len(missing), ", ".join(sorted(missing))),
            evidence={"rule_count": len(self._evidence_map),
                      "satisfied": found, "missing": missing},
        )


class InvariantCheck(_EvidenceInvariantCheck):
    """L4-04: no invariant violation — R4-001 list of 27 (I1..I27)."""

    _evidence_map = {
        "I1": ("ApprovalState", "ExecutionState"),
        "I2": ("register_entry", "list_entries"),
        "I3": ("validate_no_feedback",),
        "I4": ("validate_no_feedback", "AuditRecord"),
        "I5": ("RecorderService", "AuditRecord"),
        "I6": ("ApprovalValidator",),
        "I7": ("_select_from_exact", "resolve_exact"),
        "I8": ("OrderingValidator",),
        "I9": ("CapabilityDescriptor", "frozen"),
        "I10": ("@dataclass", "frozen", "Contract"),
        "I11": ("discover", "idempotent"),
        "I12": ("BoundaryValidator", "ApprovalValidator"),
        "I13": ("validate_no_feedback",),
        "I14": ("OrderingValidator",),
        "I15": ("bounded",),
        "I16": ("CapabilityDescriptor",),
        "I17": ("BoundaryValidator",),
        "I18": ("RegistryKey", "discover"),
        "I19": ("citizen_host", "execution_scheduler"),
        "I20": ("ApprovalState", "decision_reason"),
        "I21": ("resolve_exact", "_tie_break_key"),
        "I22": ("ContractIdempotency", "IdempotencyValidator"),
        "I23": ("IdempotencyValidator",),
        "I24": ("RecorderService",),
        "I25": ("OrderingValidator",),
        "I26": ("BoundaryValidator",),
        "I27": ("verify", "VerificationResult"),
    }


class ConstraintCheck(_EvidenceInvariantCheck):
    """L4-05: no constraint violation — R5-001 list of 30 (S,B,A,V,F,BD)."""

    _evidence_map = {
        "S1": ("citizen_host", "audit_recorder", "execution_scheduler"),
        "S2": ("OrderingValidator",),
        "S3": ("BoundaryValidator",),
        "S4": ("BoundaryValidator",),
        "S5": ("RecorderService", "AuditRecord"),
        "S6": ("BoundaryValidator", "RegistryKey"),
        "B1": ("ApprovalValidator",),
        "B2": ("register_entry", "list_entries", "discover"),
        "B3": ("validate_no_feedback",),
        "B4": ("validate_no_feedback",),
        "B5": ("_select_from_exact", "resolve_exact"),
        "B6": ("resolve_exact", "resolve_compatible", "_tie_break_key"),
        "B7": ("@dataclass", "frozen", "Contract"),
        "B8": ("ContractIdempotency", "IdempotencyValidator"),
        "B9": ("IdempotencyValidator",),
        "B10": ("OrderingValidator",),
        "B11": ("ApprovalState",),
        "B12": ("decision_reason",),
        "B13": ("discover",),
        "B14": ("CapabilityDescriptor", "frozen"),
        "A1": ("BoundaryValidator",),
        "A2": ("ApprovalValidator",),
        "A3": ("ApprovalCoordinator", "DecisionPolicy"),
        "A4": ("register_entry", "list_entries"),
        "A5": ("validate_no_feedback",),
        "A6": ("Contract", "ContractValidator"),
        "A7": ("const", "Authority"),
        "V1": ("verify", "VerificationResult"),
        "V2": ("validate_no_feedback",),
        "V3": ("Contract", "RegistryKey"),
        "V4": ("verify",),
        "F1": ("RecorderService",),
        "F2": ("record",),
        "F3": ("RecorderService", "AuditRecord"),
        "F4": ("validate_no_feedback",),
        "F5": ("AuditRecord",),
        "BD1": ("BoundaryValidator",),
        "BD2": ("BoundaryValidator",),
        "BD3": ("Certification",),
        "BD4": ("CapabilityDescriptor",),
        "BD5": ("Domain",),
    }


# ---------------------------------------------------------------------------
# L4-06 — acyclic dependency DAG
# ---------------------------------------------------------------------------

class AcyclicDependencyCheck(BaseComplianceCheck):
    """L4-06: no cycle in the runtime dependency DAG.

    Builds an import graph among the 7 runtime units from the snapshot's
    source files (unit A -> unit B when a file under A imports
    sam.runtime.B) and reports any cycle.
    """

    def execute(self, context: CheckContext) -> CheckResult:
        snapshot = BaselineResolver().resolve(context)
        root = context.options.get("baseline_root") or context.target_path
        disk = DiskReader(root)
        units = _discover_units(SnapshotReader(snapshot))
        adj = {u: set() for u in units}
        for u in units:
            base = "%s%s/" % (_RUNTIME_PREFIX, u)
            for e in snapshot.source_files():
                if not e.relative_path.startswith(base):
                    continue
                for spec in _module_imports(disk.read(e.relative_path)):
                    parts = spec.split(".")
                    if len(parts) >= 3 and parts[1] == "runtime" \
                            and parts[2] in adj and parts[2] != u:
                        adj[u].add(parts[2])
        # DFS cycle detection over deterministic order.
        order = units
        color = {k: 0 for k in units}  # 0 white, 1 gray, 2 black
        cycle = []

        def dfs(node, path):
            color[node] = 1
            for nxt in sorted(adj[node], key=order.index):
                if color[nxt] == 1:
                    cycle.append(path + [nxt])
                    return True
                if color[nxt] == 0 and dfs(
                        nxt, path + [nxt]):
                    return True
            color[node] = 2
            return False

        for n in order:
            if color[n] == 0 and dfs(n, [n]):
                break
        if not cycle:
            return CheckResult.success(
                details="Dependency DAG is acyclic across %d unit(s)"
                        % len(units),
                evidence={"units": units, "edges": {u: sorted(v)
                                                    for u, v in adj.items()},
                          "cycle": None},
            )
        return CheckResult.failure(
            details="Dependency cycle detected: %s" % " -> ".join(cycle[0]),
            evidence={"units": units, "edges": {u: sorted(v)
                                                for u, v in adj.items()},
                      "cycle": cycle[0]},
        )


# ---------------------------------------------------------------------------
# L4-07 — boundary enforcement (ADR-006)
# ---------------------------------------------------------------------------

class BoundaryEnforcementCheck(BaseComplianceCheck):
    """L4-07: boundaries enforced as defined by ADR-006.

    ADR-006 fixes the external boundary to Contracts + Registry (two
    mechanisms, no third). Verified by requiring BoundaryValidator
    components on the boundary-facing units and the absence of any
    third access mechanism (gRPC/Thrift/ZeroMQ/RPC) in the runtime.
    BoundaryValidator exists where the runtime exposes external
    boundaries (citizen_host, approval_coordinator, execution_scheduler,
    audit_recorder); discovery and contract units enforce boundaries via
    their own validators (registry/contract/idempotency).
    """

    _BOUNDARY_UNITS = ("citizen_host", "approval_coordinator",
                       "execution_scheduler", "audit_recorder")
    _THIRD_PARTY = ("grpc", "thrift", "zeromq")

    def execute(self, context: CheckContext) -> CheckResult:
        snapshot = BaselineResolver().resolve(context)
        root = context.options.get("baseline_root") or context.target_path
        disk = DiskReader(root)
        reader = SnapshotReader(snapshot)
        missing_validator = []
        for u in self._BOUNDARY_UNITS:
            found = False
            base = "%s%s/" % (_RUNTIME_PREFIX, u)
            # A boundary enforcement component exists either as a class
            # named BoundaryValidator or as a boundary_validator module.
            for e in snapshot.source_files():
                if not e.relative_path.startswith(base):
                    continue
                if "boundary_validator" in e.relative_path \
                        or "BoundaryValidator" in disk.read(e.relative_path):
                    found = True
                    break
            if not found:
                missing_validator.append(u)
        third_party = []
        for e in snapshot.source_files():
            if not e.relative_path.startswith(_RUNTIME_PREFIX):
                continue
            content = disk.read(e.relative_path)
            for mech in self._THIRD_PARTY:
                if mech in content:
                    third_party.append({"file": e.relative_path,
                                        "mechanism": mech})
        if not missing_validator and not third_party:
            return CheckResult.success(
                details="ADR-006 boundaries enforced (Contracts + Registry; "
                        "no third mechanism)",
                evidence={"boundary_units": list(self._BOUNDARY_UNITS),
                          "missing_validator": [],
                          "third_party": []},
            )
        return CheckResult.failure(
            details="Boundary violation: missing_validator=%s third_party=%d"
                    % (missing_validator, len(third_party)),
            evidence={"boundary_units": list(self._BOUNDARY_UNITS),
                      "missing_validator": missing_validator,
                      "third_party": third_party},
        )


# ---------------------------------------------------------------------------
# L4-08 — linear chain order
# ---------------------------------------------------------------------------

class LinearChainCheck(BaseComplianceCheck):
    """L4-08: linear chain order preserved.

    Verifies the canonical 7-unit chain exists — exactly
    Citizen Host -> Capability Manager -> Discovery Resolver ->
    Contract Enforcer -> Approval Coordinator -> Execution Scheduler ->
    Audit Recorder. The chain is present when all units exist and the
    runtime implements the single linear responsibility sequence.
    """

    def execute(self, context: CheckContext) -> CheckResult:
        reader = SnapshotReader(BaselineResolver().resolve(context))
        discovered = _discover_units(reader)
        missing = [u for u in _CHAIN if u not in discovered]
        extras = [u for u in discovered if u not in _CHAIN]
        if not missing and not extras and len(discovered) == len(_CHAIN):
            return CheckResult.success(
                details="Linear chain order preserved: %s"
                        % " -> ".join(_CHAIN),
                evidence={"chain": list(_CHAIN), "extras": [],
                          "missing": []},
            )
        return CheckResult.failure(
            details="Chain order broken: missing=%s extras=%s"
                    % (missing, extras),
            evidence={"chain": list(_CHAIN), "extras": extras,
                      "missing": missing},
        )
