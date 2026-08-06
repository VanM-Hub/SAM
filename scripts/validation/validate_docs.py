#!/usr/bin/env python3
"""Validate documentation: check required docs exist, CHANGELOG up to date, README version match.

Usage:
    python scripts/validation/validate_docs.py
    python scripts/validation/validate_docs.py --report
"""

import os
import sys
import json
import re

SAM_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "sam")
if not os.path.isdir(SAM_SRC):
    SAM_SRC = os.path.join("D:", os.sep, "Project AI", "SAM", "src", "sam")
REPO_ROOT = os.path.dirname(os.path.dirname(SAM_SRC))

SCORE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "reports", "architecture_docs_score.json")

# Required documentation files
REQUIRED_ARCH_DOCS = [
    "Architecture_Rulebook.md",
    "Forbidden_Dependencies.md",
    "Public_API.md",
    "Dependency_Map.md",
    "Pipeline_Specification.md",
    "DTO_Catalog.md",
    "Extension_Points.md",
    "Entry_Points.md",
    "Layer_Validation.md",
    "Module_Ownership.md",
]

REQUIRED_ADR_FOLDER = "docs/adr"
REQUIRED_RELEASE_DOCS = ["docs/releases/manifest.md"]
# version-history.md tidak lagi wajib: SAM 1.0 adalah rilis pertama, sehingga
# belum ada riwayat versi untuk dicatat (lihat CHANGELOG.md).
REQUIRED_DIAGRAMS = [
    "01_subsystem_overview.html",
    "02_pipeline_overview.html",
    "09_runtime_kernel.html",
]

def _has_adr_metadata(path):
    """Check that an ADR file has the required metadata headers.

    An ADR must at minimum declare its decision: either a **Status:** line
    (typical) or a Decision section. Date and Deciders are encouraged but the
    hard requirement is that the file is not an empty placeholder.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return False
    lower = text.lower()
    has_status = "**status:**" in lower or "status:" in lower
    has_decision = "## decision" in lower or "decision:" in lower
    return has_status or has_decision


def scan():
    errors = []
    warnings = []

    arch_dir = os.path.join(REPO_ROOT, "docs", "architecture")

    # 1. Check required architecture docs
    if not os.path.isdir(arch_dir):
        errors.append(f"MISSING: docs/architecture/ directory")
    else:
        for doc in REQUIRED_ARCH_DOCS:
            path = os.path.join(arch_dir, doc)
            if not os.path.isfile(path):
                errors.append(f"MISSING ARCH DOC: {doc}")

    # 2. Check required diagrams
    for d in REQUIRED_DIAGRAMS:
        path = os.path.join(arch_dir, d)
        if not os.path.isfile(path):
            warnings.append(f"MISSING DIAGRAM: {d}")
    # Check all 10 diagrams
    for i in range(1, 11):
        num = f"{i:02d}"
        path = os.path.join(arch_dir, f"{num}_*.html")
        import glob
        if not list(glob.glob(os.path.join(arch_dir, f"{num}_*.html"))):
            warnings.append(f"MISSING DIAGRAM: {num}_*.html")

    # 3. Check ADR folder
    adr_dir = os.path.join(REPO_ROOT, "docs", "adr")
    if not os.path.isdir(adr_dir):
        errors.append("MISSING: docs/adr/ directory")
    else:
        adr_files = [f for f in os.listdir(adr_dir) if f.startswith("ADR-") and f.endswith(".md")]
        if not adr_files:
            errors.append("NO ADR FILES in docs/adr/")
        else:
            # Validate ADR consistency: unique numbers + required metadata.
            # Per Van (C2): nominal numbers are NOT required to be sequential.
            # In a living repository it is normal for ADRs to be superseded,
            # withdrawn, or intentionally never published. The validator checks
            # consistency (no duplicate numbers, valid metadata), not sequence.
            seen = set()
            for f in adr_files:
                m = re.search(r'ADR-(\d+)', f)
                if m:
                    num = int(m.group(1))
                    if num in seen:
                        errors.append(f"DUPLICATE ADR number {num} (two files claim ADR-{num})")
                    seen.add(num)
                path = os.path.join(adr_dir, f)
                if not _has_adr_metadata(path):
                    errors.append(f"INVALID ADR METADATA: {f} (missing Status/Date/Decision)")

    # 4. Check release docs
    for doc in REQUIRED_RELEASE_DOCS:
        path = os.path.join(REPO_ROOT, doc)
        if not os.path.isfile(path):
            warnings.append(f"MISSING RELEASE DOC: {doc}")

    # 5. Check README version matches pyproject
    pyproject_path = os.path.join(REPO_ROOT, "pyproject.toml")
    readme_path = os.path.join(REPO_ROOT, "README.md")
    if os.path.isfile(pyproject_path):
        with open(pyproject_path, "r", encoding="utf-8") as f:
            pyproject = f.read()
        m = re.search(r'version = "([^"]+)"', pyproject)
        pp_version = m.group(1) if m else "unknown"
    else:
        errors.append("MISSING: pyproject.toml")
        pp_version = "unknown"

    if os.path.isfile(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
        # Look for version (vX.Y.Z or X.Y.Z) in README
        rm_versions = re.findall(r'v?\d+\.\d+\.\d+', readme)
        if pp_version not in " ".join(rm_versions):
            warnings.append(f"README version mismatch: pyproject.toml has {pp_version} but README has {rm_versions[:3]}")

    # 6. Check CHANGELOG has latest version
    changelog_path = os.path.join(REPO_ROOT, "CHANGELOG.md")
    if os.path.isfile(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            changelog = f.read()
        if pp_version not in changelog:
            errors.append(f"CHANGELOG missing entry for version {pp_version}")
    else:
        errors.append("MISSING: CHANGELOG.md")

    result = {
        "errors": errors,
        "warnings": warnings,
        "pass": len(errors) == 0,
    }
    return result

def main():
    result = scan()
    if "--report" in sys.argv:
        os.makedirs(os.path.dirname(SCORE_FILE), exist_ok=True)
        with open(SCORE_FILE, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Report written to {SCORE_FILE}")
    if result["errors"]:
        for e in result["errors"]:
            print(f"❌ {e}")
        print(f"\n❌ FAILED: {len(result['errors'])} documentation errors")
        sys.exit(1)
    if result["warnings"]:
        for w in result["warnings"]:
            print(f"⚠️  {w}")
    print(f"✅ PASS: documentation valid")
    return 0

if __name__ == "__main__":
    main()
