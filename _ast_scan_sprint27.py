"""AST Scan untuk Sprint 27 — verifikasi constraint arsitektur."""

import ast
import os
import sys

guardian_dir = "src/sam/operations/brain/guardian"
violations = []

for fname in sorted(os.listdir(guardian_dir)):
    if not fname.endswith(".py") or fname == "__init__.py":
        continue
    fpath = os.path.join(guardian_dir, fname)
    with open(fpath) as f:
        src = f.read()

    tree = ast.parse(src)

    # Hanya cek di code nodes (bukan docstring/comment)
    code_lines = set()
    for node in ast.walk(tree):
        # Skip docstrings
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if hasattr(node, "lineno"):
            code_lines.add(node.lineno)

    # Import check
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                if "domain" in mod or "repository" in mod or "storage" in mod:
                    violations.append(("DOMAIN/REPO/STORAGE", fname, mod))
        elif isinstance(node, ast.ImportFrom):
            if node.module and (
                "domain" in node.module
                or "repository" in node.module
                or "storage" in node.module
            ):
                violations.append(("DOMAIN/REPO/STORAGE", fname, node.module))

    # Check execution keywords in actual code lines (skip docstrings/comments)
    for i, line in enumerate(src.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('"') or stripped.startswith("#"):
            continue  # skip docstring/comment lines
        if i not in code_lines and '"' not in stripped and "#" not in stripped:
            # might be docstring, skip
            pass
        if i in code_lines:
            if "threading" in stripped and "import" in stripped:
                violations.append(("THREADING", fname, f"line {i}: {stripped}"))
            if "asyncio" in stripped and "import" in stripped:
                violations.append(("ASYNCIO", fname, f"line {i}: {stripped}"))

if violations:
    for vtype, fname, detail in violations:
        print(f"VIOLATION [{vtype}] {fname}: {detail}")
    sys.exit(1)
else:
    guardian_files = [f for f in os.listdir(guardian_dir) if f.endswith(".py")]
    print(f"AST SCAN PASSED — {len(guardian_files)} guardian files, 0 violations")
