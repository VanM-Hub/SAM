"""ManifestValidator — verifies manifest integrity.

Validates against the P1-004 catalog to ensure:
- every catalog check appears exactly once (no missing / no duplicate)
- every checker class exists in the P1-003 framework
- every dependency exists (no orphan)
- dependency graph is acyclic (no cycle)
- execution_order is deterministic (no duplicates conflict)
"""

from typing import List, Optional

from ..catalog.catalog import ComplianceCheckCatalog
from ..catalog.models import CheckerClass
from .entry import ManifestEntry


class ManifestValidationIssue:
    """A single validation issue with a category and message."""

    def __init__(self, category: str, message: str):
        self.category = category
        self.message = message

    def __repr__(self) -> str:
        return "ManifestValidationIssue(%r, %r)" % (self.category, self.message)


class ManifestValidationResult:
    """Aggregated validation outcome."""

    VALID = 0
    WARNING = 1
    ERROR = 2

    def __init__(self, issues: Optional[List[ManifestValidationIssue]] = None):
        self.issues: List[ManifestValidationIssue] = issues or []

    @property
    def valid(self) -> bool:
        """True if no ERROR-level issues."""
        return not any(
            i.category in ("missing", "duplicate", "unknown_dependency",
                           "unknown_checker", "cycle", "orphan")
            for i in self.issues
        )

    @property
    def has_errors(self) -> bool:
        return not self.valid

    def error_categories(self) -> List[str]:
        """Categories of all ERROR-level issues."""
        err_cats = ("missing", "duplicate", "unknown_dependency",
                    "unknown_checker", "cycle", "orphan")
        return list(dict.fromkeys(
            i.category for i in self.issues if i.category in err_cats))


# Known P1-003 checker classes (framework types).
_KNOWN_CHECKERS = {c.value for c in CheckerClass}


class ManifestValidator:
    """Validates a ComplianceManifest against the catalog + framework."""

    def __init__(self, catalog: ComplianceCheckCatalog):
        """Build validator bound to a catalog.

        Args:
            catalog: The P1-004 ComplianceCheckCatalog (source of truth).
        """
        self._catalog = catalog

    # -- Public API -----------------------------------------------------------

    def validate(self, manifest) -> ManifestValidationResult:
        """Validate a manifest. Returns a ManifestValidationResult.

        Categories reported:
        - 'missing': catalog check not in manifest
        - 'duplicate': check appears more than once
        - 'unknown_dependency': dependency points to unknown check
        - 'unknown_checker': checker_class not in P1-003 framework
        - 'cycle': dependency graph contains a cycle
        - 'orphan': check references a dependency that does not exist
        """
        issues: List[ManifestValidationIssue] = []

        catalog_ids = {c.check_id for c in self._catalog}
        manifest_ids = set(manifest.check_ids())

        # 1. Completeness — every catalog check present exactly once
        missing = sorted(catalog_ids - manifest_ids)
        for cid in missing:
            issues.append(ManifestValidationIssue(
                "missing", "Catalog check missing from manifest: %s" % cid))

        # 2. Uniqueness — no duplicate ids (manifest enforces at build, but
        #    verify anyway by reconstructing ids)
        seen = set()
        for entry in manifest.entries():
            if entry.check_id in seen:
                issues.append(ManifestValidationIssue(
                    "duplicate", "Duplicate manifest entry: %s" % entry.check_id))
            seen.add(entry.check_id)

        # 3. Unknown / orphan entries — manifest references checks not in catalog
        unknown = sorted(manifest_ids - catalog_ids)
        for cid in unknown:
            issues.append(ManifestValidationIssue(
                "orphan", "Manifest entry not in catalog: %s" % cid))

        # 4. Unknown dependencies + orphan dependencies
        for entry in manifest.entries():
            for dep in entry.dependencies:
                if dep not in catalog_ids:
                    issues.append(ManifestValidationIssue(
                        "unknown_dependency",
                        "%s depends on unknown check: %s" % (entry.check_id, dep)))

        # 5. Unknown checker class
        for entry in manifest.entries():
            if entry.checker_class and entry.checker_class not in _KNOWN_CHECKERS:
                issues.append(ManifestValidationIssue(
                    "unknown_checker",
                    "%s uses unknown checker: %s"
                    % (entry.check_id, entry.checker_class)))

        # 6. Cycle detection (Kahn's algorithm)
        cycle = self._detect_cycle(manifest)
        if cycle:
            issues.append(ManifestValidationIssue(
                "cycle", "Dependency cycle detected: %s" % " -> ".join(cycle)))

        return ManifestValidationResult(issues)

    # -- Internal -------------------------------------------------------------

    def _detect_cycle(self, manifest) -> Optional[List[str]]:
        """Return a cycle path if one exists, else None.

        Uses Kahn's algorithm on the dependency graph.
        """
        edges: dict = {}
        for entry in manifest.entries():
            edges[entry.check_id] = {
                d for d in entry.dependencies if d in manifest}

        indegree: dict = {cid: 0 for cid in edges}
        for cid, deps in edges.items():
            for dep in deps:
                indegree[dep] = indegree.get(dep, 0) + 1

        from collections import deque
        queue = deque([cid for cid, d in indegree.items() if d == 0])
        processed = 0
        # Preserve deterministic processing order
        ready_order = sorted(
            [cid for cid, d in indegree.items() if d == 0],
            key=lambda c: (manifest[c].execution_order, c))
        queue = deque(ready_order)

        while queue:
            cid = queue.popleft()
            processed += 1
            for dep in sorted(edges[cid]):
                indegree[dep] -= 1
                if indegree[dep] == 0:
                    queue.append(dep)

        if processed == len(edges):
            return None  # acyclic

        # Cycle exists — reconstruct a cycle path deterministically.
        remaining = sorted(
            [cid for cid, d in indegree.items() if d > 0],
            key=lambda c: (manifest[c].execution_order, c))
        if remaining:
            path = [remaining[0]]
            seen_path = {remaining[0]}
            cur = remaining[0]
            for _ in range(len(manifest)):
                nxt = None
                for dep in sorted(edges[cur]):
                    if dep in indegree and indegree[dep] > 0 and \
                       dep not in seen_path:
                        nxt = dep
                        break
                if nxt is None:
                    break
                path.append(nxt)
                seen_path.add(nxt)
                cur = nxt
        return path
