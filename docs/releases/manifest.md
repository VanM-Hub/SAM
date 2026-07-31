# SAM Manifest

```
Repository:   github.com/VanM-Hub/SAM
License:      Apache-2.0
Python:       >=3.8 (tested on 3.10, 3.11, 3.12)
Status:       Active Development
Current:      v12.0.0 - Phase XII (Orchestration Runtime)
Next:         v13.0.0 - Real Connector Implementations
Framework:    Python
Build:        setuptools
Test:         pytest (unit 1421 + integration 48 + api 28 + e2e 110)
Lint:         ruff
CI:           GitHub Actions (core + server + desktop)
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
| Connector Runtime | `src/sam/connectors/` | 77 | Preview-only |
| Orchestration Runtime | `src/sam/orchestrator/` | 78 | Plan-only |

## Dependencies

| Group | Packages | Use |
|-------|----------|-----|
| core | structlog, pydantic | Logging, validation |
| console | rich, typer, pyyaml | CLI |
| desktop | PySide6 | GUI |
| server | fastapi, uvicorn, httpx, jinja2, aiosqlite | Web |
| dev | pytest, ruff, build, wheel | Dev tooling |
