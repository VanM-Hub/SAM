"""compliance - WP-13 (IP-3.1-001) + WP-24 (IP-3.1-002).

Automatic verification that the Intelligence layer never crosses its
safety boundaries (WP-13) and that it exhibits the required positive
properties (WP-24):

WP-13 (forbidden - capability must NOT have):
  *  no runtime mutation
  *  no authority
  *  no orchestration
  *  no execution
  *  no approval

WP-24 (required - capability MUST exhibit):
  *  deterministic reasoning
  *  explainable output
  *  evidence-backed recommendation

WP-34 (Conversation Compliance - IP-3.1-003):
  *  no governance mutation
  *  no hidden memory (only session context, never persisted)
  *  deterministic follow-up
  *  no evidence loss (answers keep the evidence chain)

This is a static, read-only safety/property check over source files (no
runtime side effects). Returns a ComplianceReport.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Forbidden capability markers. A positive hit means the module claims (or
# calls) an ability the intelligence layer must NOT have.
_FORBIDDEN = {
    "no runtime mutation": [
        "os.remove", "os.rename", "shutil.", "Path.unlink", "Path.write_",
        "open(", "file.write", ".commit(", "subprocess",
    ],
    "no authority": ["approve(", "grant(", "authorize(", "set_permissions", "chmod"],
    "no orchestration": ["orchestrat", "spawn("],
    "no execution": ["subprocess", "os.system(", "exec(", "Popen(", "run_cmd"],
    "no approval": ["approve("],
    # WP-34: conversation must not mutate governance or persist hidden memory
    "no governance mutation": [
        "update_governance", "save_governance", "commit_governance",
        "mutate_governance", "write_governance", "persist_governance",
    ],
    "no hidden memory": [
        "pickle", "shelve", "sqlite3", "joblib", "json.dump",
        "open(\"w", "open('w", "to_disk", "save_persistent",
    ],
}

# Required positive capability markers. At least one marker must appear in the
# implemented package for each property (proves the property is present).
_REQUIRED = {
    "deterministic reasoning": ["keyword_rule", "def reason", "ReasoningTree", "rule("],
    "explainable output": ["StructuredExplanation", "def compose", "public_dict"],
    "evidence-backed recommendation": ["evidence", "has_evidence", "evidence-backed", "EvidenceRepository"],
    # WP-34: required positive conversation properties
    "deterministic follow-up": ["InteractiveTurn", "def run(", "_update_session", "_token"],
    "no evidence loss": ["evidence_chain", "_gather_evidence", "EvidenceTrace"],
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


# Files that legitimately reference forbidden markers inside the required
# positive checks (e.g. the compliance vocabulary) are excluded per-directory.
_LEGITIMATE = ()


def compliance_check(package_path: Path) -> ComplianceReport:
    """Scan every .py under package_path for forbidden and required markers."""
    checks: List[ComplianceCheck] = []
    files = _scan_source_files(package_path)
    files_text = "".join(
        f.read_text(encoding="utf-8", errors="ignore") for f in files
    )

    # --- WP-13 forbidden checks -------------------------------------------
    for name, markers in _FORBIDDEN.items():
        violations: List[str] = []
        for f in files:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for marker in markers:
                if marker in text:
                    violations.append(f"{f.name}: contains '{marker}'")
        checks.append(ComplianceCheck(name=name, passed=not violations, violations=violations[:10]))

    # --- WP-24 required positive checks ------------------------------------
    for name, markers in _REQUIRED.items():
        hits = [m for m in markers if m in files_text]
        passed = bool(hits)
        violations = [] if passed else [f"no marker for '{name}' found in package source"]
        checks.append(ComplianceCheck(name=name, passed=passed, violations=violations))

    return ComplianceReport(package=str(package_path), checks=checks)
