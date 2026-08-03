"""FileAbsentCheck — verifies that a file does NOT exist at a given path.

Deterministic: same path + same filesystem → same result.
"""

from __future__ import annotations

import os

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult


class FileAbsentCheck(BaseComplianceCheck):
    """Checks that a file does NOT exist at a relative path.

    Config fields:
        path: str — relative path from target_path to check.
    """

    def __init__(self, path: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = path

    @property
    def path(self) -> str:
        return self._path

    def execute(self, context: CheckContext) -> CheckResult:
        full_path = os.path.join(context.target_path, self._path)

        if os.path.exists(full_path):
            return CheckResult.failure(
                details="File SHOULD NOT exist: %s" % self._path,
                evidence={"path": full_path, "exists": True},
            )

        return CheckResult.success(
            details="File correctly absent: %s" % self._path,
            evidence={"path": full_path, "exists": False},
        )

    def to_config(self) -> dict:
        config = super().to_config()
        config["path"] = self._path
        return config
