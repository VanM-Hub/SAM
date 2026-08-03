"""SourceAbsentCheck — verifies source files do NOT contain forbidden patterns.

Deterministic: same files + same pattern → same result.
"""

from __future__ import annotations

import glob
import os
import re

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult


class SourceAbsentCheck(BaseComplianceCheck):
    """Checks that source files do NOT contain a forbidden pattern.

    Config fields:
        file_pattern: str — glob pattern for files to scan.
        forbidden_pattern: str — regex or literal string to avoid.
        is_regex: bool — whether forbidden_pattern is a regex (default: True).
    """

    def __init__(
        self,
        file_pattern: str,
        forbidden_pattern: str,
        is_regex: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._file_pattern = file_pattern
        self._forbidden_pattern = forbidden_pattern
        self._is_regex = is_regex

    @property
    def file_pattern(self) -> str:
        return self._file_pattern

    @property
    def forbidden_pattern(self) -> str:
        return self._forbidden_pattern

    def execute(self, context: CheckContext) -> CheckResult:
        full_glob = os.path.join(context.target_path, self._file_pattern)
        recursive = "**" in self._file_pattern
        files = sorted(glob.glob(full_glob, recursive=recursive))

        if not files:
            return CheckResult.success(
                details="No files to scan for pattern: %s" % self._file_pattern,
                evidence={"file_pattern": self._file_pattern, "files_found": 0},
            )

        violations = []
        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except (OSError, UnicodeDecodeError):
                continue

            if self._is_regex:
                found = re.findall(self._forbidden_pattern, content, re.MULTILINE)
            else:
                found = [self._forbidden_pattern] if self._forbidden_pattern in content else []

            for match in found:
                violations.append({"file": os.path.relpath(fpath, context.target_path), "match": str(match)})

        if not violations:
            return CheckResult.success(
                details="No forbidden pattern '%s' found in %d file(s)"
                % (self._forbidden_pattern, len(files)),
                evidence={
                    "file_pattern": self._file_pattern,
                    "forbidden_pattern": self._forbidden_pattern,
                    "violations": [],
                    "files_found": len(files),
                },
            )

        return CheckResult.failure(
            details="Forbidden pattern '%s' found %d time(s) in %d file(s)"
            % (self._forbidden_pattern, len(violations), len(files)),
            evidence={
                "file_pattern": self._file_pattern,
                "forbidden_pattern": self._forbidden_pattern,
                "violations": violations,
                "violation_count": len(violations),
                "files_found": len(files),
            },
        )

    def to_config(self) -> dict:
        config = super().to_config()
        config["file_pattern"] = self._file_pattern
        config["forbidden_pattern"] = self._forbidden_pattern
        config["is_regex"] = self._is_regex
        return config
