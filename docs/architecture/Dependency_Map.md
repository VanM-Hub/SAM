# Dependency Map

## Subsystem Dependency Graph

```
  approval                  --> events
  cli                       --> autonomy, cluster, contracts, dos, evolution, federation, guardian, mission, runtime, service, web
  cluster                   --> cognition
  collaboration             --> core, persistence
  confidence                --> persistence
  desktop                   --> operations
  dos                       --> contracts
  evidence                  --> events
  evolution                 --> institutional, persistence
  execution                 --> core, reasoning, runtime
  healing                   --> cognitive, confidence, evolution, execution, governance, institutional, persistence, reasoning
  institutional             --> persistence
  mission                   --> contracts
  operations                --> intelligence, telemetry
  patterns                  --> knowledge
  persistence               --> approval, evidence, knowledge, patterns, recommendations
  recommendations           --> events
  reporting                 --> events, persistence
  runtime                   --> evidence, knowledge, models, sdk, validation
  runtime_kernel            --> execution
  sdk                       --> runtime
  strategy                  --> persistence, reasoning
  tuning                    --> evolution
  workflow                  --> events, models, persistence, reporting, runtime
```

**Cyclic dependency detected:** NO (false positive in initial scan — A->B edges created empty B entries)

## Cross-Subsystem Dependency Count

| Subsystem | Depends On | Depended By |
|-----------|-----------|-------------|
| `approval` | 1 | 1 |
| `autonomy` | 0 | 1 |
| `cli` | 11 | 0 |
| `cluster` | 1 | 1 |
| `cognition` | 0 | 1 |
| `cognitive` | 0 | 1 |
| `collaboration` | 2 | 0 |
| `confidence` | 1 | 1 |
| `contracts` | 0 | 3 |
| `core` | 0 | 2 |
| `desktop` | 1 | 0 |
| `dos` | 1 | 1 |
| `events` | 0 | 5 |
| `evidence` | 1 | 2 |
| `evolution` | 2 | 3 |
| `execution` | 3 | 2 |
| `federation` | 0 | 1 |
| `governance` | 0 | 1 |
| `guardian` | 0 | 1 |
| `healing` | 8 | 0 |
| `institutional` | 1 | 2 |
| `intelligence` | 0 | 1 |
| `knowledge` | 0 | 3 |
| `mission` | 1 | 1 |
| `models` | 0 | 2 |
| `operations` | 2 | 1 |
| `patterns` | 1 | 1 |
| `persistence` | 5 | 8 |
| `reasoning` | 0 | 3 |
| `recommendations` | 1 | 1 |
| `reporting` | 2 | 1 |
| `runtime` | 5 | 4 |
| `runtime_kernel` | 1 | 0 |
| `sdk` | 1 | 1 |
| `service` | 0 | 1 |
| `strategy` | 2 | 0 |
| `telemetry` | 0 | 1 |
| `tuning` | 1 | 0 |
| `validation` | 0 | 1 |
| `web` | 0 | 1 |
| `workflow` | 5 | 0 |

## Forbidden Dependency Scan

Scanned for: threading, socket, multiprocessing, http, subprocess, asyncio, selectors

- `asyncio` in `autonomous/executor.py`: `import asyncio`
- `asyncio` in `cli/autonomous.py`: `import asyncio`
- `asyncio` in `cli/autonomy_app.py`: `import asyncio`
- `asyncio` in `cli/cluster_app.py`: `import asyncio`
- `asyncio` in `cli/events.py`: `import asyncio`
- `asyncio` in `cli/evolution_app.py`: `import asyncio`
- `asyncio` in `cli/federation_app.py`: `import asyncio`
- `asyncio` in `cli/guardian.py`: `import asyncio`
- `asyncio` in `cli/intelligence.py`: `import asyncio`
- `asyncio` in `cli/logs.py`: `import asyncio`
- `asyncio` in `cli/openclaw.py`: `import asyncio`
- `asyncio` in `cli/service.py`: `import asyncio`
- `asyncio` in `cluster/distributor.py`: `import asyncio`
- `asyncio` in `cluster/heartbeat.py`: `import asyncio`
- `asyncio` in `collaboration/protocol.py`: `import asyncio`
- `asyncio` in `core/clock.py`: `import asyncio`
- `asyncio` in `core/daemon.py`: `import asyncio`
- `asyncio` in `core/event_bus.py`: `import asyncio`
- `asyncio` in `core/scheduler.py`: `import asyncio`
- `asyncio` in `core/service_manager.py`: `import asyncio`
- `asyncio` in `execution/engine.py`: `import asyncio`
- `asyncio` in `guardian/pipeline.py`: `import asyncio`
- `asyncio` in `launcher/host_launcher.py`: `import asyncio`
- `threading` in `launcher/host_launcher.py`: `import threading`
- `subprocess` in `launcher/version.py`: `import subprocess`
- `asyncio` in `openclaw/connection.py`: `import asyncio`
- `asyncio` in `operations/health.py`: `import asyncio`
- `threading` in `operations/brain/multi_source.py`: `import threading`
- `threading` in `operations/brain/scheduler.py`: `import threading`
- `threading` in `operations/presentation/console/notification_center.py`: `import threading`
- `asyncio` in `operations/providers/runtime.py`: `import asyncio`
- `asyncio` in `persistence/database.py`: `import asyncio`
- `asyncio` in `plugin/health.py`: `import asyncio`
- `asyncio` in `plugin/lifecycle.py`: `import asyncio`
- `asyncio` in `runtime/coordinator.py`: `import asyncio`
- `asyncio` in `runtime/shutdown.py`: `import asyncio`
- `subprocess` in `service/manager.py`: `import subprocess`
- `subprocess` in `service/manager.py`: `import subprocess`
- `subprocess` in `service/manager.py`: `import subprocess`
- `subprocess` in `service/manager.py`: `import subprocess`
- `asyncio` in `service/windows.py`: `import asyncio`
- `threading` in `storage/__init__.py`: `import threading`
- `asyncio` in `telemetry/collector.py`: `import asyncio`
- `asyncio` in `telemetry/service.py`: `import asyncio`
- `asyncio` in `telemetry/stream.py`: `import asyncio`
- `asyncio` in `tuning/autotuner.py`: `import asyncio`
- `threading` in `tuning/metrics.py`: `import threading`
- `asyncio` in `web/server.py`: `import asyncio`

## Key Findings

1. Architecture is **pipeline-oriented**: Guardian -> Decision -> Approval -> Activation -> Execution -> Runtime Kernel
2. **Runtime Kernel** orchestrates all subsystems via bridges (no direct coupling)
3. No cyclic dependencies at subsystem level
4. No forbidden async/thread/network dependencies in core subsystems
5. Main dependency hub: `operations.brain.decision` (depends on multiple subsystems)