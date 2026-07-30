#!/usr/bin/env python3
"""Validate repository structure: naming conventions, required files, file placement.

Usage:
    python scripts/validation/validate_structure.py
    python scripts/validation/validate_structure.py --report
"""

import os
import sys
import json
import re

SAM_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "sam")
if not os.path.isdir(SAM_SRC):
    SAM_SRC = os.path.join("D:", os.sep, "Project AI", "SAM", "src", "sam")
REPO_ROOT = os.path.dirname(os.path.dirname(SAM_SRC))

SCORE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "reports", "architecture_structure_score.json")

# Required files at repo root
REQUIRED_ROOT_FILES = ["README.md", "CHANGELOG.md", "pyproject.toml", "LICENSE", ".gitignore"]

# Required docs folders
REQUIRED_DOCS = ["docs/architecture", "docs/adr", "docs/reports", "docs/releases", "docs/sprint-reports"]

# Packages that must have __init__.py with __all__
DEFINED_SUBSYSTEMS = [
    "sam.guardian.live",
    "sam.approval",
    "sam.activation",
    "sam.operational_brain",
    "sam.runtime_kernel",
    "sam.execution.runtime",
    "sam.operations.brain.decision",
]

def scan():
    errors = []
    warnings = []

    # 1. Check required root files
    for f in REQUIRED_ROOT_FILES:
        path = os.path.join(REPO_ROOT, f)
        if not os.path.isfile(path):
            errors.append(f"MISSING ROOT FILE: {f}")

    # 2. Check required docs folders
    for folder in REQUIRED_DOCS:
        path = os.path.join(REPO_ROOT, folder)
        if not os.path.isdir(path):
            errors.append(f"MISSING DOCS FOLDER: {folder}")

    # 3. Check naming conventions
    for root, dirs, files in os.walk(SAM_SRC):
        dirs[:] = [d for d in dirs if not d.startswith("__pycache__") and d != ".git"]
        for f in files:
            if not f.endswith(".py"):
                continue
            if f == "__init__.py":
                continue
            # Check snake_case
            if re.search(r'[A-Z]', f):
                errors.append(f"NAMING VIOLATION: {os.path.relpath(os.path.join(root, f), SAM_SRC)} — contains uppercase")
            # Check singular
            # Bridge naming
            if f.startswith("conversation_") or f.startswith("dashboard_"):
                pass  # valid
            # Test naming
            if f.startswith("test_") or f.startswith("test_sprint"):
                pass  # valid

    # 4. Check __init__.py with __all__ for defined subsystems
    for subsystem in DEFINED_SUBSYSTEMS:
        # subsystem is like "sam.guardian.live" — skip the "sam" prefix
        parts = subsystem.split(".")[1:] if subsystem.startswith("sam.") else subsystem.split(".")
        pkg_path = os.path.normpath(os.path.join(SAM_SRC, *parts))
        init_file = os.path.join(pkg_path, "__init__.py")
        if not os.path.isfile(init_file):
            # Try alternate: maybe the path is correct but file not found
            errors.append(f"MISSING __init__.py: {subsystem}/ at {init_file}")
            continue
        with open(init_file, "r", encoding="utf-8") as f:
            content = f.read()
        if "__all__" not in content:
            warnings.append(f"MISSING __all__: {subsystem}/__init__.py")

    # 5. Check no __pycache__
    for root, dirs, files in os.walk(REPO_ROOT):
        if "__pycache__" in dirs:
            warnings.append(f"__pycache__ found: {os.path.relpath(os.path.join(root, '__pycache__'), REPO_ROOT)}")

    # 6. Adapter/plugin directory check
    plugin_path = os.path.join(SAM_SRC, "plugin")
    if not os.path.isdir(plugin_path):
        warnings.append("MISSING: sam/plugin/")

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
        print(f"\n❌ FAILED: {len(result['errors'])} structure errors")
        sys.exit(1)
    if result["warnings"]:
        for w in result["warnings"]:
            print(f"⚠️  {w}")
    print(f"✅ PASS: structure valid")
    return 0

if __name__ == "__main__":
    main()
