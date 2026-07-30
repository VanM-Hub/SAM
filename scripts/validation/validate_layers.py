#!/usr/bin/env python3
"""Validate layer dependencies against Architecture Rulebook LR rules.

Usage:
    python scripts/validation/validate_layers.py
    python scripts/validation/validate_layers.py --report
"""

import ast
import os
import sys
import json

SAM_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "sam")
if not os.path.isdir(SAM_SRC):
    SAM_SRC = os.path.join("D:", os.sep, "Project AI", "SAM", "src", "sam")

# Layer definitions — top-down
LAYER_PRESENTATION = ["sam.cli", "sam.desktop", "sam.api", "sam.hosting"]
LAYER_RUNTIME = ["sam.guardian.live", "sam.operations.brain.decision", "sam.approval",
                 "sam.activation", "sam.execution", "sam.operational_brain"]
LAYER_COORDINATOR = ["sam.runtime_kernel"]
LAYER_INFRASTRUCTURE = ["sam.plugin", "sam.storage", "sam.persistence", "sam.service"]

# Layer hierarchy: higher index = lower layer (lower layer cannot import higher layer)
LAYER_ORDER = {
    "presentation": 0,
    "runtime": 1,
    "coordinator": 1,  # Same level as runtime (horizontal coordination)
    "infrastructure": 5,
    "unknown": 99,
}

# Map packages to layer
PACKAGE_LAYER = {}
for p in LAYER_PRESENTATION:
    PACKAGE_LAYER[p] = "presentation"
for p in LAYER_RUNTIME:
    PACKAGE_LAYER[p] = "runtime"
for p in LAYER_COORDINATOR:
    PACKAGE_LAYER[p] = "coordinator"
for p in LAYER_INFRASTRUCTURE:
    PACKAGE_LAYER[p] = "infrastructure"

# Auto-populate sub-packages in each layer
for root, dirs, files in os.walk(SAM_SRC):
    dirs[:] = [d for d in dirs if not d.startswith("__pycache__")]
    for f in files:
        if not f.endswith(".py"):
            continue
        full = os.path.join(root, f)
        rel = os.path.relpath(full, SAM_SRC).replace(os.sep, ".").replace(".py", "")
        pkg_name = "sam." + rel
        for prefix, layer in list(PACKAGE_LAYER.items()):
            if pkg_name.startswith(prefix):
                PACKAGE_LAYER[pkg_name] = layer
                break

SCORE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "reports", "architecture_layer_score.json")

def get_package(filepath):
    parts = os.path.normpath(filepath).split(os.sep)
    try:
        src_index = parts.index("sam")
        return ".".join(parts[src_index:]).replace(".py", "")
    except ValueError:
        return None

def get_layer(package):
    for prefix, layer in PACKAGE_LAYER.items():
        if package.startswith(prefix):
            return layer
    return "unknown"

def classify_import(target_mod, source_layer):
    target_layer = None
    for prefix, layer in PACKAGE_LAYER.items():
        if target_mod.startswith(prefix):
            target_layer = layer
            break
    if target_layer is None:
        return None
    if source_layer == "unknown":
        return None

    src_rank = LAYER_ORDER.get(source_layer, 99)
    tgt_rank = LAYER_ORDER.get(target_layer, 99)

    # Coordinator↔Runtime is same rank — allowed
    if src_rank == tgt_rank:
        return None
    if src_rank > tgt_rank:
        return f"VIOLATION: '{source_layer}' (rank {src_rank}) imports '{target_layer}' (rank {tgt_rank}) — lower layer importing higher layer"
    return None

def scan():
    violations = []
    total = 0
    for root, dirs, files in os.walk(SAM_SRC):
        dirs[:] = [d for d in dirs if not d.startswith("__pycache__")]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            package = get_package(path)
            if not package:
                continue
            source_layer = get_layer(package)
            total += 1
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        v = classify_import(alias.name, source_layer)
                        if v:
                            violations.append(f"{v}: {package} -> {alias.name} (line {node.lineno})")
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    v = classify_import(mod, source_layer)
                    if v:
                        violations.append(f"{v}: {package} -> {mod} (line {node.lineno})")
    return violations, total

def main():
    violations, total = scan()
    if "--report" in sys.argv:
        result = {
            "files_scanned": total,
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
        print(f"\n❌ FAILED: {len(violations)} layer violations (scanned {total} files)")
        sys.exit(1)
    print(f"✅ PASS: 0 layer violations (scanned {total} files)")
    return 0

if __name__ == "__main__":
    main()
