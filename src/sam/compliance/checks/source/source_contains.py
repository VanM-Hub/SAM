"""SourceContainsCheck — verifies source files contain required patterns.

Deterministic: same files + same pattern → same result.
Supports glob patterns and regex search.
"""

from __future__ import annotations

import glob
import os
import re

from typing import List

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult


class SourceContainsCheck(BaseComplianceCheck):
    """Checks that source files contain a required pattern.

    Config fields:
        file_pattern: str — glob pattern for files to scan (e.g. 'src/**/*.py').
        search_pattern: str — regex or literal string to find.
        is_regex: bool — whether search_pattern is a regex (default: True).
        required_count: int — minimum number of matches required (default: 1).
    """

    def __init__(
        self,
        file_pattern: str,
        search_pattern: str,
        is_regex: bool = True,
        required_count: int = 1,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._file_pattern = file_pattern
        self._search_pattern = search_pattern
        self._is_regex = is_regex
        self._required_count = required_count

    @property
    def file_pattern(self) -> str:
        return self._file_pattern

    @property
    def search_pattern(self) -> str:
        return self._search_pattern

    def execute(self, context: CheckContext) -> CheckResult:
        full_glob = os.path.join(context.target_path, self._file_pattern)
        recursive = "**" in self._file_pattern
        files = sorted(glob.glob(full_glob, recursive=recursive))

        if not files:
            return CheckResult.failure(
                details="No files matched pattern: %s" % self._file_pattern,
                evidence={"file_pattern": self._file_pattern, "files_found": 0},
            )

        matches = []
        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except (OSError, UnicodeDecodeError):
                continue

            if self._is_regex:
                found = re.findall(self._search_pattern, content, re.MULTILINE)
            else:
                found = [self._search_pattern] if self._search_pattern in content else []

            for match in found:
                matches.append({"file": os.path.relpath(fpath, context.target_path), "match": str(match)})

        if len(matches) >= self._required_count:
            return CheckResult.success(
                details="Found %d match(es) for '%s' in %d file(s) (required: %d)"
                % (len(matches), self._search_pattern, len(files), self._required_count),
                evidence={
                    "file_pattern": self._file_pattern,
                    "search_pattern": self._search_pattern,
                    "matches": matches,
                    "match_count": len(matches),
                    "files_found": len(files),
                    "required_count": self._required_count,
                },
            )

        return CheckResult.failure(
            details="Found %d match(es), required %d. Pattern: '%s' in '%s'"
            % (len(matches), self._required_count, self._search_pattern, self._file_pattern),
            evidence={
                "file_pattern": self._file_pattern,
                "search_pattern": self._search_pattern,
                "matches": matches,
                "match_count": len(matches),
                "files_found": len(files),
                "required_count": self._required_count,
            },
        )

    def to_config(self) -> dict:
        config = super().to_config()
        config["file_pattern"] = self._file_pattern
        config["search_pattern"] = self._search_pattern
        config["is_regex"] = self._is_regex
        config["required_count"] = self._required_count
        return config
