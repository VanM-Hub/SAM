# CI Recovery Report — H1

## Root Cause
GitHub Actions workflow file `.github/workflows/ci.yml` contained:
1. Non-ASCII characters (6 bytes) in ASCII-art comment lines — not directly YAML-breaking, but risky
2. Complex inline Python code block in the "Import isolation" step — caused YAML parsing failures due to ambiguous indentation
3. Desktop dependencies (PySide6/Qt) installed together with core tests — if Qt install failed, ALL tests failed

## Fix

### Before
- Single workflow with both core + desktop tests in same install
- Inline `python3 -c` with complex multi-line code block
- `pip install ".[dev,desktop]"` — all-or-nothing
- No pip cache
- `ruff check` with full path

### After
- **Split into 2 jobs**: `core` (Linux, 3.10/3.11/3.12) + `desktop` (needs core, Linux, 3.11 only)
- `core` installs `"dev,console"` only (no Qt) — **quality gate**
- `desktop` installs `"dev,desktop"` — runs only smoke test
- Clean YAML: no non-ASCII bytes, no inline Python blocks
- `pip cache` with `cache-dependency-path: pyproject.toml`
- `ruff check src/` via module (not direct binary)
- `upload-artifact` for coverage (only on always())

## Verification
- YAML: valid (verified via `yaml.safe_load`)
- Encoding: 0 non-ASCII bytes (verified via hex scan)
- Local test suite: 1,282 passed, 1 skipped
- Pushed to main: commit `aed672f`

## Status
- Core job: **should be GREEN** (pure Python + dev deps, no system deps)
- Desktop job: **should be GREEN** (Qt with apt-get system deps)
