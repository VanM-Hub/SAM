# SAM Manifest

```
Repository:   github.com/VanM-Hub/SAM
License:      Apache-2.0
Python:       >=3.8 (tested on 3.10, 3.11, 3.12)
Status:       Active Development
Current:      v10.0.0 — Phase X (Runtime Kernel)
Next:         v10.0.1 — Repository Stabilization
Framework:    Python
Build:        setuptools
Test:         pytest ~9,661 tests
Lint:         ruff
CI:           GitHub Actions (core + desktop)
```

## Subsystem Map

| Subsystem | Path | Files | Status |
|-----------|------|-------|--------|
| Foundation | `src/sam/` | Various | Stable |
| Operational Brain | `src/sam/operational_brain/` | ~15 | Stable |
| Guardian Live | `src/sam/guardian/live/` | ~60 | Stable |
| Decision Runtime | `src/sam/operations/brain/decision/` | ~80 | Stable |
| Activation | `src/sam/activation/` | ~48 | Stable |
| Execution | `src/sam/execution/runtime/` | ~40 | Stable |
| Approval | `src/sam/approval/` | ~50 | Stable |
| Runtime Kernel | `src/sam/runtime_kernel/` | 69 | Preview-only |

## Dependencies

| Group | Packages | Use |
|-------|----------|-----|
| core | structlog, pydantic | Logging, validation |
| console | rich, typer, pyyaml | CLI |
| desktop | PySide6 | GUI |
| server | fastapi, uvicorn, httpx, jinja2, aiosqlite | Web |
| dev | pytest, ruff, build, wheel | Dev tooling |
