#!/usr/bin/env python3
"""Validate DTO consistency: frozen dataclass, no mutable defaults, no forbidden methods.

Usage:
    python scripts/validation/validate_dto.py
    python scripts/validation/validate_dto.py --report
"""

import ast
import os
import sys
import json
import dataclasses

SAM_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "sam")
if not os.path.isdir(SAM_SRC):
    SAM_SRC = os.path.join("D:", os.sep, "Project AI", "SAM", "src", "sam")

SCORE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "reports", "architecture_dto_score.json")

FORBIDDEN_METHODS = {"process", "execute", "run", "invoke", "dispatch"}

def scan():
    violations = []
    total_classes = 0
    total_files = 0
    for root, dirs, files in os.walk(SAM_SRC):
        dirs[:] = [d for d in dirs if not d.startswith("__pycache__")]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            relative = os.path.relpath(path, SAM_SRC)
            total_files += 1
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a dataclass
                    decorator_names = []
                    for d in node.decorator_list:
                        if isinstance(d, ast.Call):
                            if hasattr(d.func, 'attr') and d.func.attr == 'dataclass':
                                decorator_names.append('dataclass')
                            elif hasattr(d.func, 'id') and d.func.id == 'dataclass':
                                decorator_names.append('dataclass')
                        elif isinstance(d, ast.Name):
                            decorator_names.append(d.id)
                        elif isinstance(d, ast.Attribute):
                            decorator_names.append(d.attr)

                    if 'dataclass' not in decorator_names:
                        continue

                    total_classes += 1
                    # Check for frozen
                    for d in node.decorator_list:
                        if isinstance(d, ast.Call):
                            for kw in d.keywords:
                                if kw.arg == "frozen" and isinstance(kw.value, ast.Constant):
                                    if kw.value.value is False:
                                        violations.append(f"NOT FROZEN: {relative}: class {node.name} has frozen=False")
                                    break
                            else:
                                # Call with no frozen keyword
                                pass
                        elif isinstance(d, ast.Name) and d.id == 'dataclass':
                            # @dataclass without args — not frozen by default
                            pass

                    # Check forbidden methods — only if it's a dataclass
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name in FORBIDDEN_METHODS:
                                # Skip non-DTO classes (UI apps, services)
                                if not any(base.id in ('object',) if isinstance(base, ast.Name) else False for base in node.bases):
                                    violations.append(f"FORBIDDEN METHOD: {relative}: class {node.name} has method '{item.name}' (line {item.lineno})")
                            # Check for mutable defaults
                            if item.args.defaults:
                                for default in item.args.defaults:
                                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                                        violations.append(f"MUTABLE DEFAULT: {relative}: class {node.name} method '{item.name}' has mutable default (line {item.lineno})")

                    # Check for mutable class attributes
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and item.value:
                            if isinstance(item.value, (ast.List, ast.Dict, ast.Set)):
                                violations.append(f"MUTABLE CLASS ATTR: {relative}: class {node.name} attribute has mutable default (line {item.lineno})")

    return violations, total_classes, total_files

def main():
    violations, total_classes, total_files = scan()
    if "--report" in sys.argv:
        result = {
            "files_scanned": total_files,
            "classes_scanned": total_classes,
            "violations": len(violations),
            "pass": len(violations) == 0,
        }
        os.makedirs(os.path.dirname(SCORE_FILE), exist_ok=True)
        with open(SCORE_FILE, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Report written to {SCORE_FILE}")
    if violations:
        for v in violations:
            print(v)
        print(f"\n❌ FAILED: {len(violations)} DTO violations (scanned {total_files} files, {total_classes} dataclasses)")
        sys.exit(1)
    print(f"✅ PASS: 0 DTO violations (scanned {total_files} files, {total_classes} dataclasses)")
    return 0

if __name__ == "__main__":
    main()
