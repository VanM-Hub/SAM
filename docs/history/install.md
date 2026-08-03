# SAM Desktop Qt — Install & Run Guide

## Prerequisites

- **Python 3.8+** (tested up to 3.12)
- **pip** (or any PEP 517 compatible installer)
- Optional but recommended: a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate    # Linux/macOS
```

---

## Install — Console Only (CLI)

```bash
pip install ".[console]"
```

Then launch:

```bash
sam-console
# or
python -m sam.cli.main
```

No PySide6 required. Runs on any Python 3.8+ environment.

---

## Install — Desktop Qt (GUI)

```bash
pip install ".[desktop]"
```

PySide6 (Qt6) will be installed automatically.

> ⏳ First install downloads Qt shared libraries (~200 MB). This is normal.

Then launch:

```bash
sam-desktop
# or
python -m sam.desktop.main
```

### Linux Notes

Some Linux distros need system Qt libraries:

```bash
# Debian/Ubuntu
sudo apt install libxcb-cursor0 libegl1-mesa libgl1-mesa-glx

# Fedora
sudo dnf install qt6-qtbase-gui
```

### macOS Notes

PySide6 ships as a wheel — no extra system dependencies needed.
If you see "Qt platform plugin 'cocoa' not found", update pip and retry.

---

## Install — Development

```bash
pip install -e ".[dev,desktop]"
```

This installs:
- SAM core + desktop Qt
- pytest, pytest-cov, pytest-asyncio
- ruff (linter)

---

## Install — All Extras

```bash
pip install ".[all]"        # console + desktop + server
pip install ".[all,dev]"    # all extras + dev tools
```

---

## Verify Installation

```bash
pip list | grep sam-ops
# Should show: sam-ops 4.12.0
```

---

## Troubleshooting

### "PySide6 is not installed"

Desktop widgets display a runtime message but don't crash. Core/conversation API
still works. Install with:

```bash
pip install ".[desktop]"
```

### "Cannot open display" on Linux

You need a display server (X11/Wayland). For headless testing only, use:

```bash
QT_QPA_PLATFORM=offscreen sam-desktop
```

### Windows — DLL load failed

If you see "DLL load failed while importing shiboken6", try:

```bash
pip uninstall PySide6 shiboken6
pip install ".[desktop]"
```

### Windows — Console shows Chinese characters

Append before launch:

```cmd
set PYTHONIOENCODING=utf-8
```

### Import errors in custom code

If you write extensions that import from `sam.operations.presentation.desktop.qt`,
ensure `PYTHONPATH` includes the `src/` directory:

```bash
export PYTHONPATH=/path/to/sam/src:$PYTHONPATH   # Linux
set PYTHONPATH=C:\path\to\sam\src;%PYTHONPATH%   # Windows
```

---

## Architecture Note

```
sam[core]        → conversation_api, pydantic models, structlog
sam[console]     → typer, rich, pyyaml (no Qt)
sam[desktop]     → PySide6 (adds Qt GUI)
sam[server]      → fastapi, uvicorn, httpx (optional API)
```

Desktop does not require console. Console does not require desktop.
Server is independent. All share the same domain layer.
