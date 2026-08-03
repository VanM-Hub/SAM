# Compatibility Matrix

**Version:** v1.0.0  
**Date:** 2026-07-25  
**Status:** ✅ Verified

---

## Python Versions

| Version | Status | Notes |
|---|---|---|
| **3.8** | ✅ **Supported** | Active development; `asyncio.to_thread` polyfill in `database.py` |
| **3.9** | ✅ Supported | Natively has `asyncio.to_thread` |
| **3.10** | ✅ Supported | — |
| **3.11** | ✅ Supported | — |
| **3.12** | ✅ **Recommended** | Best performance, latest language features |
| **3.13+** | ⚠️ Untested | Likely compatible; not yet verified |

## Dependencies

| Package | Min Version | Max Version | Purpose | CVE Status |
|---|---|---|---|---|
| Python stdlib | 3.8 | — | Core runtime | ✅ No known CVEs |
| `sqlite3` | stdlib | — | Database engine | ✅ Bundled |
| `structlog` | 20.0 | latest | Structured logging | ✅ Low risk |
| `typer` | 0.4 | latest | CLI framework | ✅ Low risk |
| `pydantic` | 2.0 | 2.x | Data validation | ⚠️ Deprecation warnings only |
| `pyyaml` (optional) | 5.0 | latest | YAML knowledge import | ✅ Optional |
| `psutil` (optional) | 5.0 | latest | System metrics collection | ✅ Optional |
| `pytest` (dev) | 7.0 | latest | Test framework | ✅ Dev only |
| `pytest-asyncio` (dev) | 0.21 | latest | Async test support | ✅ Dev only |

## OpenClaw Compatibility

| OpenClaw Version | SAM Compatibility | Notes |
|---|---|---|
| 1.x | ✅ Compatible | SAM runs as an independent process |
| Not required | ✅ **Standalone** | SAM does not require OpenClaw to run |

## Hardware Requirements (Minimum)

| Resource | Minimum | Recommended |
|---|---|---|
| RAM | 128 MB | 512 MB+ |
| CPU | 1 core | 2+ cores |
| Disk | 100 MB | 500 MB+ |
| Database | sqlite3 (local) | — |

## Operating System

| OS | Status | Notes |
|---|---|---|
| **Windows 10/11** | ✅ Tested | Development host |
| **Linux (Ubuntu 20.04+)** | ✅ Compatible | Production target |
| **macOS 12+** | ⚠️ Compatible (untested) | Should work via Python |

## Network

| Protocol | Port | Purpose |
|---|---|---|
| Internal (IPC) | — | No network required for standalone mode |
| HTTP (future) | 8080 (default) | REST API (planned for v1.1) |

---

*Document prepared for SAM v1.0.0 release.*
