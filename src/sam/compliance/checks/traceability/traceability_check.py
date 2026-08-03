"""TraceabilityCheck — verifies artifact traceability chain.

Checks that every artifact in the target traces back to a specification,
ADR, or baseline document. Deterministic: same files + same rules →
same result.
"""

from __future__ import annotations

import glob
import os

from typing import Dict, List, Optional

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult


class TraceabilityCheck(BaseComplianceCheck):
    """Checks that artifacts are traceable to baseline documents.

    Config fields:
        file_pattern: str — glob for files to check.
        required_refs: List[str] — required reference patterns.
        optional_refs: List[str] — optional reference patterns.
        min_refs: int — minimum number of references required per file.

    The check scans each file for references to baseline documents
    (specs, ADRs, architecture docs). References are matched by
    prefix (e.g., 'CITIZEN_SPEC', 'ADR-', 'R4-001').
    """

    def __init__(
        self,
        file_pattern: str,
        required_refs: List[str] = None,
        optional_refs: List[str] = None,
        min_refs: int = 1,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._file_pattern = file_pattern
        self._required_refs = list(required_refs or [])
        self._optional_refs = list(optional_refs or [])
        self._min_refs = min_refs

    def execute(self, context: CheckContext) -> CheckResult:
        full_glob = os.path.join(context.target_path, self._file_pattern)
        recursive = "**" in self._file_pattern
        files = sorted(glob.glob(full_glob, recursive=recursive))

        if not files:
            return CheckResult.success(
                details="No files to check: %s" % self._file_pattern,
                evidence={"file_pattern": self._file_pattern, "files_found": 0},
            )

        all_refs = set(self._required_refs + self._optional_refs)
        missing = []
        for fpath in files:
            rel = os.path.relpath(fpath, context.target_path)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except (OSError, UnicodeDecodeError):
                continue

            found = [ref for ref in all_refs if ref in content]

            if len(found) < self._min_refs:
                missing_req = [r for r in self._required_refs if r not in found]
                missing.append({
                    "file": rel,
                    "found_refs": found,
                    "found_count": len(found),
                    "missing_required": missing_req,
                })

        if not missing:
            return CheckResult.success(
                details="All %d file(s) have sufficient traceability refs (min %d)"
                % (len(files), self._min_refs),
                evidence={
                    "file_pattern": self._file_pattern,
                    "files_found": len(files),
                    "missing": [],
                },
            )

        return CheckResult.failure(
            details="%d file(s) missing traceability refs (min %d)"
            % (len(missing), self._min_refs),
            evidence={
                "file_pattern": self._file_pattern,
                "files_found": len(files),
                "missing": missing,
                "missing_count": len(missing),
                "min_refs": self._min_refs,
            },
        )

    def to_config(self) -> dict:
        config = super().to_config()
        config["file_pattern"] = self._file_pattern
        config["required_refs"] = list(self._required_refs)
        config["optional_refs"] = list(self._optional_refs)
        config["min_refs"] = self._min_refs
        return config
