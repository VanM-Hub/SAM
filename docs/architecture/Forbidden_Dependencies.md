# Forbidden Dependency Matrix

> **SAM v10.2.0** — Architecture Governance Baseline
> **File:** `docs/architecture/Forbidden_Dependencies.md`

---

**Legend:**
- ✅ = allowed
- ❌ = forbidden
- 🤝 = friend module (boleh import ini)
- 🔌 = extension point (plugin/provider/adapter via registry)

---

## 1. `sam.guardian.live`

| Target | Rule | Notes |
|--------|------|-------|
| `events` | ✅ | Base event bus |
| `sam.guardian.*` | ✅ | Sibling guardian modules |
| `sam.operations.brain.decision.*` | ❌ | Must go through DecisionInput DTO |
| `sam.approval.*` | ❌ | Must go through bridge |
| `sam.activation.*` | ❌ | Must go through bridge |
| `sam.execution.*` | ❌ | Must go through bridge |
| `sam.runtime_kernel.*` | ❌ | Must go through bridge |
| `sam.cli.*` | ❌ | Presentation layer |
| `sam.desktop.*` | ❌ | Presentation layer |
| `asyncio` | ❌ | Synchronous runtime |
| `threading` | ❌ | Synchronous runtime |
| `requests` | ❌ | No network |
| `sam.launcher.*` | 🤝 | Launcher is allowed for all |

## 2. `sam.operations.brain.decision`

| Target | Rule | Notes |
|--------|------|-------|
| `sam.guardian.live.*` | 🤝 | DecisionInput consumer |
| `sam.approval.*` | 🤝 | Decision activates approval |
| `sam.events.*` | ✅ | Event bus |
| `sam.activation.*` | ❌ | Must go through bridge |
| `sam.execution.*` | ❌ | Must go through bridge |
| `sam.runtime_kernel.*` | ❌ | Must go through bridge |
| `sam.cli.*` | ❌ | Presentation layer |
| `asyncio` | ❌ | Synchronous |
| `threading` | ❌ | Synchronous |

## 3. `sam.approval`

| Target | Rule | Notes |
|--------|------|-------|
| `sam.events.*` | ✅ | Event bus |
| `sam.guardian.*` | ❌ | Must go through bridge |
| `sam.operations.brain.decision.*` | ❌ | Approval is independent |
| `sam.activation.*` | ❌ | Must go through bridge |
| `sam.execution.*` | ❌ | Must go through bridge |
| `sam.runtime_kernel.*` | ❌ | Must go through bridge |
| `asyncio` | ❌ | Synchronous approval |

## 4. `sam.operational_brain`

| Target | Rule | Notes |
|--------|------|-------|
| `sam.events.*` | ✅ | Event bus |
| `sam.guardian.*` | ❌ | Bridge only |
| `sam.approval.*` | ❌ | Bridge only |
| `sam.activation.*` | ❌ | Bridge only |
| `sam.execution.*` | ❌ | Bridge only |
| `asyncio` | ❌ | Synchronous |

## 5. `sam.activation`

| Target | Rule | Notes |
|--------|------|-------|
| `sam.operational_brain.*` | 🤝 | Receives operational plans |
| `sam.events.*` | ✅ | Event bus |
| `sam.guardian.*` | ❌ | Bridge only |
| `sam.approval.*` | ❌ | Bridge only |
| `sam.execution.*` | ❌ | Bridge only |
| `sam.runtime_kernel.*` | ❌ | Bridge only |
| `asyncio` | ❌ | Synchronous |

## 6. `sam.execution.runtime`

| Target | Rule | Notes |
|--------|------|-------|
| `sam.activation.*` | 🤝 | ActivationPackage consumer |
| `sam.events.*` | ✅ | Event bus |
| `sam.guardian.*` | ❌ | Bridge only |
| `sam.approval.*` | ❌ | Bridge only |
| `sam.runtime_kernel.*` | ❌ | Bridge only |
| `asyncio` | ❌ | Synchronous (preview) |

## 7. `sam.runtime_kernel`

| Target | Rule | Notes |
|--------|------|-------|
| `sam.execution.*` | 🤝 | Coordinates execution |
| `sam.events.*` | ✅ | Event bus |
| `sam.guardian.*` | ✅ | Coordinator to guardian |
| `sam.approval.*` | ✅ | Coordinator to approval |
| `sam.activation.*` | ✅ | Coordinator to activation |
| `sam.operational_brain.*` | ✅ | Coordinator to OP brain |
| `sam.desktop.*` | ✅ | Presentation access |
| `asyncio` | ❌ | Synchronous |
| `threading` | ❌ | Synchronous |

## 8. `sam.cli`

| Target | Rule | Notes |
|--------|------|-------|
| All subsystems | ✅ | Presentation can access anything |
| `asyncio` | ✅ | CLI has async capabilities |
| `threading` | ❌ | CLI should be sync where possible |

## 9. `sam.desktop`

| Target | Rule | Notes |
|--------|------|-------|
| `sam.operations.*` | ✅ | Presentation |
| All subsystems | 🤝 | Via bridges only |
| `asyncio` | ✅ | Desktop has async (Qt event loop) |
| `PySide6` | ✅ | Desktop dependency |
| `threading` | ❌ | No threading in desktop |

## 10. `sam.launcher`

| Target | Rule | Notes |
|--------|------|-------|
| All subsystems | ✅ | Launcher boots everything |
| `asyncio` | ❌ | Launcher should be sync |
| `threading` | ❌ | Launcher should be sync |

## 11. `sam.plugin`

| Target | Rule | Notes |
|--------|------|-------|
| PluginLoader → runtime | ✅ | Loads plugin |
| All runtime modules | ❌ | Plugin must use bridge interfaces |
| Plugin runtime interface | 🔌 | Via plugin host |

## 12. Forbidden Global Imports

| Import | Allowed In | Forbidden In |
|--------|-----------|--------------|
| `asyncio` | `cli/`, `desktop/`, `hosting/`, `web/`, `openclaw/`, `telemetry/`, `plugin/health/`, `plugin/lifecycle/` | All other packages |
| `threading` | `launcher/`, `operations/brain/*`, `storage/`, `tuning/` | Runtime subsystems |
| `multiprocessing` | None | All |
| `socket` | `openclaw/` | All other packages |
| `requests` | None | All |
| `subprocess` | `launcher/version.py`, `service/manager.py` | All other packages |
