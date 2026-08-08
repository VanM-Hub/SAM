# Module Ownership

Architecture Freeze v10.

---

## Subsystem Ownership Map

| Subsystem | Path | Purpose | Dependencies | Status |
|-----------|------|---------|-------------|--------|
| Guardian Live | `sam/guardian/live/` | Monitor, assess, triage runtime state | events | 🟢 Stable |
| Decision | `sam/operations/brain/decision/` | Evaluate, plan, approve, certify decisions | guardian, approval | 🟢 Stable |
| Approval | `sam/approval/` | Multi-level policy-based approval | events | 🟢 Stable |
| Operational Brain | `sam/operational_brain/` | Plan, schedule, monitor health | events | 🟢 Stable |
| Activation | `sam/activation/` | Transform decisions → packages | operational_brain | 🟢 Stable |
| Execution | `sam/execution/runtime/` | Plan, simulate, assemble execution | activation, reasoning | 🟢 Stable |
| Runtime Kernel | `sam/runtime_kernel/` | Central coordination, health, security | all subsystems | 🔵 Preview |
| CLI | `sam/cli/` | Command-line interface | launcher | 🟢 Stable |
| Desktop | `sam/desktop/` | Qt GUI | launcher, operations | 🟢 Stable |
| Plugin | `sam/plugin/` | Extension loading/discovery | runtime | 🟢 Stable |
| Launcher | `sam/launcher/` | Entry point, boot pipeline | cli, desktop, hosting | 🟢 Stable |
| Hosting | `sam/hosting/` | Windows service, Docker, systemd | runtime | 🟢 Stable |

## Legacy/Stabilized (Not Part of Architecture Freeze)

| Subsystem | Path | Notes |
|-----------|------|-------|
| `sam/runtime/` | Legacy | Pre-dates Runtime Kernel |
| `sam/reasoning/` | Legacy | Deprecated — superseded by Guardian |
| `sam/workflow/` | Legacy | Deprecated — superseded by Decision |

## Public API vs Private API

| Subsystem | Public (via `__init__.py` + `__all__`) | Private |
|-----------|--------------------------------------|---------|
| Guardian Live | ~200 exports in `__all__` | Internal classes, implementation details |
| Approval | DTOs + engines + bridges | Internal engines, dashboards |
| Activation | Builders, pipelines, packages | Internal health, window, constraints |
| Runtime Kernel | Adapters, bridges, health, coordinators | Internal state, lifecycle |
| Operations.brain.decision | Evaluators, planners, gateways, sessions | Internal submission, packaging |
| Execution.runtime | DTOs, engines, bridges | Internal monitors, simulators |
| Operational brain | Planners, schedulers, health | Internal metrics, dependencies |

## Future Extension

| Subsystem | Planned Extension |
|-----------|-----------------|
| Runtime Kernel | Full production mode (remove preview-only) |
| Connector Runtime | Phase XI — cross-subsystem connectors |
| Guardian Live | Additional situation classifiers |
| Decision | Extended certification rules |
| Approval | More policy providers |

---

## Note

Dokumen ini adalah canonical source untuk ownership & status subsystem (stable / preview / legacy-deprecated) pada Architecture Freeze v10. Perubahan struktur source tidak dilakukan tanpa rujukan ke dokumen ini.
