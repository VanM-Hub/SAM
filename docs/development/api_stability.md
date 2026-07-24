# API Stability & Deprecation Policy

**Version:** v1.0.0

---

## 1. Scope

This document defines which parts of SAM are considered **stable public API** and therefore subject to backward compatibility guarantees within the v1.x lifecycle.

## 2. Stable API (Will Not Break in v1.x)

### CLI Commands
The following CLI commands and their output formats are stable:

| Command | Stable Since | Notes |
|---|---|---|
| `sam health` | v1.0 | Output format: text + JSON |
| `sam evolution list` | v1.0 | Output format: text + JSON |
| `sam evolution show` | v1.0 | — |
| `sam cluster status` | v1.0 | — |
| `sam autonomy status` | v1.0 | — |
| `sam federation status` | v1.0 | — |
| `sam daemon start/stop/status` | v1.0 | — |

### Python Package Public API

The following module exports are considered stable:

```python
from sam.cognition import (
    CognitiveState, CognitiveStateManager,
    WorkingMemory, WorkingMemoryManager,
    ContextWindow, ContextItem,
    CognitiveSession, CognitiveSessionManager,
    AttentionManager, FocusArea,
    GoalArbitrator, GoalType,
)
from sam.healing.loop import SelfHealingLoop
from sam.evolution.policy import EvolutionPolicy
from sam.tuning.autotuner import Autotuner
from sam.autonomy import AutonomyLevel, AutonomyController, SafetyEnvelope
from sam.cluster import ClusterKnowledgeShare, ClusterStrategySync
from sam.federation import FederationManager, TrustManager
```

### Database Schema

All migration files (001–047) are stable. No existing tables or columns will be removed in v1.x. New tables and columns may be added via new migration files.

## 3. Unstable / Internal API (May Change)

The following are **internal** and may change without notice:

- All `_`-prefixed private methods and classes
- Internal database query patterns
- Log message formats
- Error messages and exception types (unless documented)
- Module structure within `src/sam/*/` (public exports are stable)
- Test fixtures and test utility functions

## 4. Deprecation Policy

### Timeline

1. **Deprecation announced** — Feature marked with `DeprecationWarning` for 2 minor versions
2. **Feature removed** — After the deprecation period

### Process

```python
import warnings
warnings.warn(
    "Feature X is deprecated since v1.2 and will be removed in v1.4. "
    "Use Feature Y instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

### Current Deprecations

| Feature | Deprecated In | Removed In | Replacement |
|---|---|---|---|
| Pydantic V1 config (`allow_mutation`) | v1.0 | v2.0 | `ConfigDict` |
| `sam.cluster.discovery` direct import | v1.0 | v1.2 | `sam.cluster.ClusterKnowledgeShare` |
| `sam.cognitive` (old module) | v1.0 | v1.2 | `sam.cognition` |

## 5. Versioning Scheme

SAM follows **Semantic Versioning 2.0**:

```
MAJOR.MINOR.PATCH
```

| Component | When to Bump |
|---|---|
| **MAJOR** | Breaking change to stable API |
| **MINOR** | New feature, no breaking changes |
| **PATCH** | Bug fix, no API changes |

**Pre-release markers:** `v1.0.0-alpha.1`, `v1.0.0-rc.1`

---

*Document prepared for SAM v1.0.0 release.*
