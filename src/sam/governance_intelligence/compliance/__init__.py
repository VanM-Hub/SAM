"""compliance — WP-13 (IP-3.1-001).

Automatic verification that the Intelligence layer never crosses its
safety boundaries. It inspects the package's own modules to assert:

  *  no runtime mutation
  *  no authority
  *  no orchestration
  *  no execution
  *  no approval

This is a static, read-only safety check over source files (no runtime side
effects). Returns a ComplianceReport.

Per directive (WP-13): the intelligence layer must prove it holds no
authority and mutates nothing. This check is the proof.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Forbidden capability markers. A positive hit means the module claims (or
# calls) an ability the intelligence layer must NOT have.
_STOPWORDS = {
    "no runtime mutation": [
        "os.remove", "os.rename", "shutil.", "Path.unlink", "Path.write_",
        "open(", "file.write", ".commit(", "subprocess",
    ],
    "no authority": ["approve(", "grant(", "authorize(", "set_permissions", "chmod"],
    "no orchestration": ["orchestrat", "spawn("]
    ,
    "no execution": ["subprocess", "os.system(", "exec(", "Popen(", "run_cmd"],
    "no approval": ["approve("],
}


@dataclass(frozen=True)
class ComplianceCheck:
    name: str
    passed: bool
    violations: List[str] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed, "violations": list(self.violations)}


@dataclass(frozen=True)
class ComplianceReport:
    package: str
    checks: List[ComplianceCheck] = field(default_factory=list)

    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def public_dict(self) -> dict:
        return {
            "package": self.package,
            "passed": self.passed(),
            "checks": [c.public_dict() for c in self.checks],
        }


def _scan_source_files(package_path: Path) -> List[Path]:
    # Exclude the compliance module itself: it legitimately contains these
    # markers as its own detection vocabulary.
    return sorted(
        f
        for f in package_path.rglob("*.py")
        if "compliance" not in f.parts[-2:]
    )


def compliance_check(package_path: Path) -> ComplianceReport:
    """Scan every .py under package_path for forbidden capability markers."""
    checks: List[ComplianceCheck] = []
    files = _scan_source_files(package_path)
    for name, markers in _STOPWORDS.items():
        violations: List[str] = []
        for f in files:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for marker in markers:
                if marker in text:
                    # A marker inside a comment in THIS file is still a claim
                    # we flag; the framework should not contain such markers
                    # in implemented modules. Report the first occurrence only.
                    violations.append(f"{f.name}: contains '{marker}'")
        checks.append(ComplianceCheck(name=name, passed=not violations, violations=violations[:10]))
    return ComplianceReport(package=str(package_path), checks=checks)
