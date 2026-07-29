# OP-410 — Connector Runtime (Sprint 35)

Dokumentasi arsitektur Connector Runtime untuk Sprint 35.

---

## 1. Runtime Architecture

Connector Runtime adalah lapisan yang mengatur siklus hidup connector, validasi capability, penegakan policy, dan health checking — semua tanpa eksekusi nyata.

```
Mission Proposal
    ↓
Execution Plan
    ↓
Connector Runtime
    ↓
Capability Check
    ↓
Policy Check
    ↓
Execution Preview
    ↓
Guardian
    ↓
Conversation
    ↓
(Human Approval)
    ↓
Real Connector (Sprint 36)
```

**Lokasi kode:** `src/sam/execution/connectors/`

---

## 2. Pipeline (ConnectorRuntime)

```
Registry → Select Connector
    ↓
Capability Validation
    ↓
Permission/Policy Validation
    ↓
Execution Preview
    ↓
Guardian Check
    ↓
Conversation DTO
```

Setiap langkah di `ConnectorRuntime` class.

---

## 3. Capability Model

10 built-in capabilities via `CapabilitySet.all_builtin()`:

| Capability | Risk Level | Requires Approval | Requires Guardian |
|---|---|---|---|
| read | low | no | no |
| search | low | no | no |
| monitor | low | no | no |
| notify | low | no | no |
| write | medium | yes | no |
| create | medium | yes | no |
| approve | medium | yes | no |
| delete | high | yes | yes |
| execute | high | yes | yes |
| rollback | high | yes | yes |

`CapabilityMatcher` untuk matching, checking risk threshold, dan approval details.

---

## 4. Policy Flow

8 minimal policies via `PolicyEvaluator`:

- **connector enabled**: filter connector types
- **connector trusted**: filter trusted connector types
- **capability allowed**: block specific capabilities (default: execute, delete)
- **approval required**: risk-based approval requirement
- **guardian required**: risk threshold for guardian review
- **read only mode**: block write operations
- **maintenance mode**: block all operations
- **connector health**: block unhealthy connectors

Semua policy menghasilkan `PolicyDecision` dengan `PolicyViolation`.

---

## 5. Health Model

Rule-based health checking via `ConnectorHealthEngine`:

5 rules:
- **availability**: connector reachable
- **configuration**: valid config
- **registration**: properly registered
- **capability completeness**: has at least one capability
- **policy compliance**: passes basic policy checks

Output: `ConnectorHealthSnapshot` and `HealthReport`.

---

## 6. Mock Connectors (preview only)

| Connector | Type | Capabilities | Preview |
|---|---|---|---|
| MockFilesystemConnector | filesystem | read, write, create, delete, search | `[PREVIEW] Read file: {path}` |
| MockRESTConnector | rest_api | read, write, create, delete, search, monitor, notify | `[PREVIEW] GET {endpoint}` |
| MockGitConnector | git | read, write, create, delete, search, rollback | `[PREVIEW] Git revert to {commit}` |
| MockShellConnector | shell | read, monitor, execute, search | `[PREVIEW] Shell execute: {cmd}` |

TIDAK ada network calls, TIDAK ada subprocess, TIDAK ada real execution.

---

## 7. Connector Lifecycle

```
1. Register (ConnectorRegistry)
       ↓
2. Create Session (ConnectorRuntime.create_session)
       ↓
3. Select Connector (ConnectorRuntime.select_connector)
       ↓
4. Validate Capability (ConnectorRuntime.validate_capability)
       ↓
5. Check Policy (PolicyEvaluator.evaluate)
       ↓
6. Compile Preview (ConnectorRuntime.compile_preview)
       ↓
7. Create Context (ConnectorRuntime.create_context)
       ↓
8. Guardian Approval (ConnectorRuntime.mark_guardian_approval)
       ↓
9. Conversation DTO (ConnectorRuntime.to_conversation_dto)
       ↓
10. Close Session (ConnectorRuntime.close_session)
```

---

## 8. Future Real Connectors (Sprint 36)

Setelah Sprint 35, real connectors bisa dibuat dengan:

- Implement `ConnectorProtocol` or extend `BaseConnector`
- Register with `ConnectorRegistry`
- All operations go through `ConnectorIntegrationPipeline`
- All operations require approval
- No auto execution

---

## 9. Files (ringkasan)

| File | Baris | Isi |
|---|---|---|
| `connector_runtime.py` | ~180 | ConnectorRuntime, ConnectorSession, ConnectorContext, ConnectorHealth |
| `connector_capability.py` | ~150 | Capability, CapabilitySet, CapabilityMatcher, CapabilityReport |
| `connector_policy.py` | ~250 | PolicyEvaluator, 8 minimal policies |
| `connector_health.py` | ~170 | ConnectorHealthEngine, HealthReport, 5 rules |
| `mock_connectors.py` | ~190 | 4 mock connectors (preview only) |
| `conversation_connector.py` | ~260 | ConversationConnectorBridge, 10 query types |
| `dashboard_connector.py` | ~130 | ConnectorDashboardBuilder, 6 DTO cards |
| `integration_connector.py` | ~220 | ConnectorIntegrationPipeline |

Signature: ZARA 🦋
