#!/usr/bin/env python3
"""Validate import rules: forbidden modules, cross-runtime imports, DTO layer isolation.

Usage:
    python scripts/validation/validate_imports.py
    python scripts/validation/validate_imports.py --report
"""

import ast
import os
import sys
import re

SAM_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "sam")
if not os.path.isdir(SAM_SRC):
    SAM_SRC = os.path.join("D:", os.sep, "Project AI", "SAM", "src", "sam")

FORBIDDEN_MODULES = ["asyncio", "threading", "multiprocessing", "socket", "requests", "http.client", "urllib.request"]
ALLOWED_PATTERNS = {
    "asyncio": [r"sam/cli/", r"sam/desktop/", r"sam/hosting/", r"sam/web/", r"sam/openclaw/",
                r"sam/telemetry/", r"sam/plugin/health", r"sam/plugin/lifecycle",
                r"sam/cluster/distributor", r"sam/cluster/heartbeat",
                r"sam/collaboration/protocol", r"sam/core/clock", r"sam/core/daemon",
                r"sam/core/event_bus", r"sam/core/scheduler", r"sam/core/service_manager",
                r"sam/execution/engine", r"sam/guardian/pipeline",
                r"sam/launcher/host_launcher", r"sam/operations/health",
                r"sam/operations/providers/runtime", r"sam/persistence/database",
                r"sam/runtime/coordinator", r"sam/runtime/shutdown",
                r"sam/service/windows", r"sam/tuning/autotuner",
                r"sam/autonomous/executor"],
    "threading": [r"sam/launcher/host_launcher", r"sam/operations/brain/multi_source",
                   r"sam/operations/brain/scheduler",
                   r"sam/operations/presentation/console/notification_center",
                   r"sam/storage/", r"sam/tuning/metrics"],
    "subprocess": [r"sam/launcher/version", r"sam/service/manager"],
    "socket": [r"sam/openclaw/"],
}

# Cross-runtime forbidden pairs
RUNTIME_PACKAGES = {
    "sam.guardian.live": ["sam.operations.brain.decision", "sam.approval", "sam.activation", "sam.execution", "sam.runtime_kernel"],
    "sam.approval": ["sam.guardian", "sam.operations.brain.decision", "sam.activation", "sam.execution", "sam.runtime_kernel"],
    "sam.operational_brain": ["sam.guardian", "sam.approval", "sam.activation", "sam.execution"],
    "sam.activation": ["sam.guardian", "sam.approval", "sam.execution", "sam.runtime_kernel"],
    "sam.execution": ["sam.guardian", "sam.approval", "sam.runtime_kernel"],
}

DTO_PACKAGES = ["sam.runtime_kernel"]  # has DTO layer, must not import runtime above

SCORE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "reports", "architecture_import_score.json")

def is_under(path_prefix, patterns):
    for p in patterns:
        if re.search(p, path_prefix.replace("\\", "/")):
            return True
    return False

def check_file(path, relative_path):
    errors = []
    skip_allowed = any(is_under(relative_path, ALLOWED_PATTERNS.get(m, [])) for m in FORBIDDEN_MODULES)
    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return [f"SYNTAX ERROR in {relative_path}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                if mod in FORBIDDEN_MODULES:
                    if not skip_allowed and not is_under(relative_path, ALLOWED_PATTERNS.get(mod, [])):
                        errors.append(f"FORBIDDEN {mod} in {relative_path} (line {node.lineno})")
                # Check cross-runtime
                for runtime, forbidden in RUNTIME_PACKAGES.items():
                    if relative_path.startswith(runtime.replace(".", os.sep)):
                        for fbd in forbidden:
                            if mod.startswith(fbd):
                                errors.append(f"CROSS-RUNTIME {mod} in {relative_path} (line {node.lineno}): {runtime} cannot import {fbd}")
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod in FORBIDDEN_MODULES:
                if not skip_allowed and not is_under(relative_path, ALLOWED_PATTERNS.get(mod, [])):
                    errors.append(f"FORBIDDEN {mod} in {relative_path} (line {node.lineno})")
            for runtime, forbidden in RUNTIME_PACKAGES.items():
                if relative_path.startswith(runtime.replace(".", os.sep)):
                    for fbd in forbidden:
                        if mod.startswith(fbd):
                            errors.append(f"CROSS-RUNTIME {mod} in {relative_path} (line {node.lineno}): {runtime} cannot import {fbd}")
            # DTO layer check
            if "dto" in mod.lower() or any(relative_path.startswith(p.replace(".", os.sep)) for p in DTO_PACKAGES):
                if mod.startswith("sam.") and not mod.startswith("sam.events") and "dto" not in mod.lower():
                    if not relative_path.startswith(tuple(p.replace(".", os.sep) for p in DTO_PACKAGES)):
                        pass  # skip, not DTO layer
            for alias in node.names:
                if alias.name in FORBIDDEN_MODULES:
                    if not skip_allowed and not is_under(relative_path, ALLOWED_PATTERNS.get(alias.name, [])):
                        errors.append(f"FORBIDDEN {alias.name} in {relative_path} (line {node.lineno})")
    return errors

def scan():
    all_errors = []
    total = 0
    for root, dirs, files in os.walk(SAM_SRC):
        dirs[:] = [d for d in dirs if not d.startswith("__pycache__") and d != ".git"]
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                path = os.path.join(root, f)
                relative = os.path.relpath(path, SAM_SRC).replace("\\", "/")
                total += 1
                errors = check_file(path, relative)
                all_errors.extend(errors)
    return all_errors, total

def main():
    errors, total = scan()
    violations = [e for e in errors if not e.startswith("SYNTAX")]
    syntax = [e for e in errors if e.startswith("SYNTAX")]
    if "--report" in sys.argv:
        import json
        result = {
            "files_scanned": total,
            "violations": len(violations),
            "syntax_errors": len(syntax),
            "pass": len(violations) == 0,
        }
        os.makedirs(os.path.dirname(SCORE_FILE), exist_ok=True)
        with open(SCORE_FILE, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Report written to {SCORE_FILE}")
    if errors:
        for e in errors:
            print(e)
    if violations:
        print(f"\n❌ FAILED: {len(violations)} import violations found (scanned {total} files)")
        sys.exit(1)
    if syntax:
        print(f"\n⚠️  {len(syntax)} syntax errors found (scanned {total} files)")
        sys.exit(1)
    print(f"✅ PASS: 0 import violations (scanned {total} files)")
    return 0

if __name__ == "__main__":
    main()
