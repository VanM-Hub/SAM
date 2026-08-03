"""ImportIllegalCheck — verifies no forbidden imports exist.

Deterministic: same files + same forbidden list → same result.
"""

from __future__ import annotations

import glob
import os
import re

from typing import List

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult


class ImportIllegalCheck(BaseComplianceCheck):
    """Checks that source files do NOT contain forbidden imports.

    Config fields:
        file_pattern: str — glob for files to scan.
        forbidden_imports: List[str] — patterns of forbidden imports.
        exclude_files: List[str] — files to skip (optional).
    """

    _IMPORT_RE = re.compile(
        r"^\s*(?:from\s+(\S+)\s+import\s+|import\s+(\S+))", re.MULTILINE
    )

    def __init__(
        self,
        file_pattern: str,
        forbidden_imports: List[str],
        exclude_files: List[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._file_pattern = file_pattern
        self._forbidden_imports = list(forbidden_imports)
        self._exclude_files = list(exclude_files or [])

    def execute(self, context: CheckContext) -> CheckResult:
        full_glob = os.path.join(context.target_path, self._file_pattern)
        recursive = "**" in self._file_pattern
        files = sorted(glob.glob(full_glob, recursive=recursive))

        if not files:
            return CheckResult.success(
                details="No files to scan: %s" % self._file_pattern,
                evidence={"file_pattern": self._file_pattern, "files_found": 0},
            )

        violations = []
        forbidden_set = set(self._forbidden_imports)

        for fpath in files:
            rel = os.path.relpath(fpath, context.target_path)
            if rel in self._exclude_files:
                continue

            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except (OSError, UnicodeDecodeError):
                continue

            for m in self._IMPORT_RE.finditer(content):
                module = m.group(1) or m.group(2)
                is_forbidden = any(
                    module == forbidden or module.startswith(forbidden + ".")
                    for forbidden in forbidden_set
                )
                if is_forbidden:
                    violations.append({"file": rel, "import": module})

        if not violations:
            return CheckResult.success(
                details="No forbidden imports found in %d file(s)" % len(files),
                evidence={
                    "file_pattern": self._file_pattern,
                    "files_found": len(files),
                    "violations": [],
                },
            )

        return CheckResult.failure(
            details="Found %d forbidden import(s) in %d file(s)"
            % (len(violations), len(files)),
            evidence={
                "file_pattern": self._file_pattern,
                "files_found": len(files),
                "violations": violations,
                "violation_count": len(violations),
            },
        )

    def to_config(self) -> dict:
        config = super().to_config()
        config["file_pattern"] = self._file_pattern
        config["forbidden_imports"] = list(self._forbidden_imports)
        config["exclude_files"] = list(self._exclude_files)
        return config
