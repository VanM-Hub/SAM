"""TestResultCheck — verifies test results (count, pass rate, existence).

Deterministic: same test directory → same result.
"""

from __future__ import annotations

import glob
import os

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult


class TestResultsCheck(BaseComplianceCheck):
    """Checks test file existence, count, and pass status.

    __test__ = False  # pytest: do not collect as test class

    Config fields:
        test_pattern: str — glob for test files (e.g. 'tests/**/test_*.py').
        min_count: int — minimum number of test files required.
        check_content: bool — whether to verify test files contain test functions.
        require_pytest_mark: bool — verify each file has a pytest import.

    This check verifies STRUCTURAL test presence, not execution.
    For execution-based verification, use a subprocess runner.
    """

    def __init__(
        self,
        test_pattern: str,
        min_count: int = 0,
        check_content: bool = True,
        require_pytest_mark: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._test_pattern = test_pattern
        self._min_count = min_count
        self._check_content = check_content
        self._require_pytest_mark = require_pytest_mark

    def execute(self, context: CheckContext) -> CheckResult:
        full_glob = os.path.join(context.target_path, self._test_pattern)
        recursive = "**" in self._test_pattern
        files = sorted(glob.glob(full_glob, recursive=recursive))

        if not files:
            return CheckResult.failure(
                details="No test files found: %s" % self._test_pattern,
                evidence={
                    "test_pattern": self._test_pattern,
                    "files_found": 0,
                    "min_count": self._min_count,
                },
            )

        issues = []
        for fpath in files:
            rel = os.path.relpath(fpath, context.target_path)

            if self._check_content:
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                except (OSError, UnicodeDecodeError):
                    issues.append({"file": rel, "issue": "Cannot read file"})
                    continue

                if "def test_" not in content:
                    issues.append({"file": rel, "issue": "No test functions found"})

                if self._require_pytest_mark and "import pytest" not in content:
                    issues.append({"file": rel, "issue": "Missing 'import pytest'"})

        total = len(files)
        ok = total - len(set(i["file"] for i in issues))

        if total < self._min_count:
            return CheckResult.failure(
                details="Found %d test file(s), minimum required: %d"
                % (total, self._min_count),
                evidence={
                    "test_pattern": self._test_pattern,
                    "files_found": total,
                    "min_count": self._min_count,
                    "issues": issues,
                },
            )

        if issues:
            return CheckResult.failure(
                details="%d/%d test file(s) have issues" % (len(issues), total),
                evidence={
                    "test_pattern": self._test_pattern,
                    "files_found": total,
                    "files_ok": ok,
                    "min_count": self._min_count,
                    "issues": issues,
                },
            )

        return CheckResult.success(
            details="All %d test file(s) pass structural check" % total,
            evidence={
                "test_pattern": self._test_pattern,
                "files_found": total,
                "files_ok": total,
                "min_count": self._min_count,
                "issues": [],
            },
        )

    def to_config(self) -> dict:
        config = super().to_config()
        config["test_pattern"] = self._test_pattern
        config["min_count"] = self._min_count
        config["check_content"] = self._check_content
        config["require_pytest_mark"] = self._require_pytest_mark
        return config
