# SAM Operations Console

**Version:** 1.0  
**Status:** Final  
**Date:** 2026-07-27  

---

## Purpose

Operations Console adalah antarmuka operasional utama SAM. CLI, GUI, dan Web Dashboard menggunakan informasi yang sama melalui Runtime API.

---

## Bab 1 — sam status

```bash
sam status
```

### Output
```
SAM Framework v1.1.0

Runtime
  State          : RUNNING
  Health         : HEALTHY
  Uptime         : 02:18:42
  Hosting        : Docker
  Boot Profile   : Production

Workspace
  Name           : default
  Location       : /opt/sam/workspace
  Version        : 1.1

Session
  Session ID     : a9e8b91d
  Started        : 2026-08-01T08:13:22Z
  Last Activity  : 2 seconds ago

Runtime
  Knowledge      : READY
  Memory         : READY
  Workflow       : IDLE
  Plugins        : 14 Loaded
  Federation     : ENABLED

Resources
  CPU            : 2.8 %
  Memory         : 418 MB
  Threads        : 19

Operations
  Pending Jobs   : 0
  Active Jobs    : 0
  Checkpoints    : 84
  Recovery       : READY

Overall Status
✓ SAM is operating normally.
```

### Exit Codes
- 0: Healthy
- 1: Degraded
- 2: Recovery
- 3: Safe Mode
- 4: Failed

---

## Bab 2 — sam monitor

```bash
sam monitor
```

### Output
```
14:02:11  Runtime Started
14:02:12  Workspace Loaded
14:02:13  Database Ready
14:02:14  Plugin Runtime Ready
14:02:15  Knowledge Runtime Ready
14:02:16  Memory Runtime Ready
14:02:17  Workflow Runtime Ready
14:02:18  Runtime READY
14:05:10  Workflow Started
14:05:15  Checkpoint Created
14:05:21  Workflow Completed
14:05:22  Memory Updated
14:05:23  Health OK
```

### Filter
```bash
sam monitor --runtime workflow
sam monitor --health
sam monitor --plugins
sam monitor --events lifecycle
```

---

## Bab 3 — sam runtime

```bash
sam runtime
```

### Output
```
Runtime Container
├── Workflow Runtime
│      Status : RUNNING
├── Plugin Runtime
│      Status : RUNNING
├── Knowledge Runtime
│      Status : READY
├── Memory Runtime
│      Status : READY
├── Cognitive Runtime
│      Status : READY
├── Federation Runtime
│      Status : RUNNING
├── Telemetry Runtime
│      Status : RUNNING
└── Monitoring Runtime
       Status : RUNNING
```

### Verbose Mode
```bash
sam runtime --verbose
```
Menambahkan: Version, Health, Started Time, Dependency, Resource Usage.

---

## Bab 4 — sam health

```bash
sam health
```

### Output
```
Overall Health
✓ HEALTHY

────────────────────────────
Runtime
✓ Runtime Container
✓ Workflow Runtime
✓ Knowledge Runtime
✓ Memory Runtime
✓ Plugin Runtime
✓ Federation Runtime
✓ Telemetry Runtime
✓ Monitoring Runtime

Infrastructure
✓ Database
✓ Workspace
✓ Session
✓ Configuration

Health Score : 100%
```

### Verbose Mode
```bash
sam health --verbose
```
Menambahkan: Last Check, Response Time, Health Provider, Failure Reason, Recovery Recommendation.

### Exit Codes
- 0: Healthy
- 1: Warning
- 2: Critical

---

## Bab 5 — sam session

```bash
sam session
```

### Output
```
Current Session
Session ID      : a9e8b91d
Workspace       : default
Started         : 2026-08-01T08:13:22Z
Last Activity   : 2026-08-01T10:41:52Z
Duration        : 2h 28m
Snapshot        : Available
Checkpoint      : #84
Recovery        : None
Runtime         : RUNNING
```

### History
```bash
sam session --history
```

### Detail
```bash
sam session <session-id>
```

---

## Bab 6 — sam recovery

```bash
sam recovery
```

### Output
```
Last Recovery
Recovery Time   : 2026-08-01T08:13:22Z
Recovered Workflow : 2
Checkpoint Used : #83
Pending Replay  : None
Status          : SUCCESS
```

---

## Bab 7 — sam plugins

```bash
sam plugins
```

### Output
```
Plugin             Status    Version    API    Health
nvidia            RUNNING    1.0.0      2.0    HEALTHY
openai            RUNNING    1.0.0      2.0    HEALTHY
anthropic         RUNNING    1.0.0      2.0    HEALTHY
ollama            DISABLED   0.5.0      1.0    DEGRADED
```

---

## Bab 8 — sam knowledge

```bash
sam knowledge
```

### Output
```
Knowledge Bases
Documents       : 1,247
Vectors         : 892
Embedding       : ENABLED
Federation      : ACTIVE
Cache           : 45.2 MB
```

---

## Bab 9 — sam memory

```bash
sam memory
```

### Output
```
Working Memory
Long Memory     : 1,234 entries
Context         : 12 KB
Attention       : 4.5 KB
Sessions        : 3 active
```

---

## Bab 10 — sam workflow

```bash
sam workflow
```

### Output
```
Running         : 2
Completed       : 142
Queue           : 3
Failed          : 0
Replay          : 0
```

---

## Bab 11 — sam events --follow

```bash
sam events --follow
```

### Output
```
13:44:21  BOOT_STARTED
13:44:22  WORKSPACE_READY
13:44:23  DATABASE_READY
13:44:24  PLUGIN_LOADED
13:44:25  READY
13:45:10  WORKFLOW_STARTED
13:45:11  CHECKPOINT_CREATED
13:45:30  WORKFLOW_COMPLETED
```
