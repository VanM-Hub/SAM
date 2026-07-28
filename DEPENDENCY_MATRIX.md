# SAM Dependency Matrix

## Runtime Dependencies — Core (100% required)

| Package | Min | Why |
|---|---|---|
| python | >=3.8 | Compatibility target |
| structlog | >=21.0 | Structured logging throughout |
| pydantic | >=1.10,<3 | All data models, schemas, DTOs |
| typing_extensions | >=4.0 (py<3.11) | Protocol, Literal, TypeAlias |

## Runtime Dependencies — Console (optional[console])

| Package | Min | Why |
|---|---|---|
| rich | >=12.0 | Terminal formatting, tables, markdown |
| typer | >=0.9 | CLI argument parsing, subcommands |
| pyyaml | >=6.0 | YAML config files |

## Runtime Dependencies — Desktop Qt (optional[desktop])

| Package | Min | Why |
|---|---|---|
| PySide6 | >=6.5 | Qt6 bindings: widgets, core, GUI |

*(PySide6 installs `shiboken6` automatically as its backend)*

## Runtime Dependencies — API Server (optional[server])

| Package | Min | Why |
|---|---|---|
| fastapi | >=0.100 | HTTP API routes |
| uvicorn | >=0.20 | ASGI server runner |
| httpx | >=0.24 | HTTP client for health/metrics |
| jinja2 | >=3.0 | Template rendering in API |
| aiosqlite | >=0.19 | Async DB access for API |

## Dev Dependencies (optional[dev])

| Package | Min | Why |
|---|---|---|
| pytest | >=7.0 | Test runner |
| pytest-cov | >=4.0 | Coverage reports |
| pytest-asyncio | >=0.21 | Async test support |
| ruff | >=0.3 | Linter + formatter |
| build | >=1.0 | Build wheel/sdist |
| wheel | >=0.40 | Build helper |
| setuptools | >=64 | Build backend |

## CI Only (not in pyproject extras)

| Package | Reason |
|---|---|
| (system) libxcb-cursor0, libegl1-mesa, libgl1-mesa-glx | Qt headless on Linux |
| actions/upload-artifact@v4 | Coverage artifact storage |
| actions/checkout@v4 | Git checkout |
| actions/setup-python@v5 | Python version matrix |

## Dependency Graph (visual)

```
sam                             ← always (structlog + pydantic)
  ├── sam[console]              ← typer, rich, pyyaml
  ├── sam[desktop]              ← PySide6
  ├── sam[server]               ← fastapi, uvicorn, httpx, jinja2, aiosqlite
  └── sam[dev]                  ← pytest, ruff, build
    
sam[all]                        ← semua extras sekaligus
sam[desktop]                    ← hanya core + PySide6 (console opsional)
sam-console                     ← core + console
sam-desktop                     ← core + desktop + console
```

## Isolation Rules

```python
# ✅ Boleh import di desktop/qt/
from PySide6.QtWidgets import ...
from sam.operations.presentation.renderer import ...
from sam.operations.presentation.desktop.layout import ...

# ❌ TIDAK BOLEH import di desktop/qt/
from sam.storage import ...
from sam.operations.executor import ...
from sam.operations.conversation_api import SAM  # domain bypass
from sam.telemetry import ...
```

## Pip Install Commands

```bash
# Minimal — hanya core (conversation API)
pip install .

# Console (CLI)
pip install ".[console]"

# Desktop Qt
pip install ".[desktop]"

# Server API
pip install ".[server]"

# Everything
pip install ".[all]"

# Development
pip install ".[dev,desktop]"

# Editable
pip install -e ".[dev,desktop]"
```
