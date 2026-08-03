"""FileExistsCheck — verifies that a file exists at a given path.

Deterministic: same path + same filesystem → same result.
"""

from __future__ import annotations

import os

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult


class FileExistsCheck(BaseComplianceCheck):
    """Checks whether a file exists at a relative path.

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

        if os.path.isfile(full_path):
            stat = os.stat(full_path)
            return CheckResult.success(
                details="File exists: %s (%d bytes)" % (self._path, stat.st_size),
                evidence={"path": full_path, "size": stat.st_size, "exists": True},
            )

        return CheckResult.failure(
            details="File NOT found: %s" % self._path,
            evidence={"path": full_path, "exists": False},
        )

    def to_config(self) -> dict:
        config = super().to_config()
        config["path"] = self._path
        return config
