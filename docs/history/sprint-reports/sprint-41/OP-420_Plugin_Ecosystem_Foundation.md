# OP-420 — Plugin Ecosystem Foundation (Sprint 41)

Dokumentasi arsitektur Plugin Ecosystem untuk Sprint 41.

---

## 1. Architecture

Plugin Ecosystem memungkinkan SAM diperluas tanpa mengubah core runtime. Plugin sandboxed, read-only by default, approval-first.

```
Registry → Loader → Policy → Runtime → Conversation → Dashboard
                    ↓
              Preview Only
```

**Lokasi kode:** `src/sam/plugins/`

---

## 2. Plugin Lifecycle

```
register() → enabled=True → execute_preview()
                                         ↓
                                  PluginResult (read-only preview)
```

- All plugins start read-only by default
- Mutable operations require approval
- No dynamic code execution (eval/exec/import string)

---

## 3. Plugin Manifest

```json
{
  "name": "Analytics Plugin",
  "version": "1.0.0",
  "author": "SAM",
  "required_version": "4.0.0",
  "read_only": true,
  "capabilities": [
    {"name": "analyze", "actions": ["read","search"], "risk_level": "low"},
    {"name": "report", "actions": ["read"], "risk_level": "low"}
  ],
  "dependencies": []
}
```

---

## 4. Registry

`PluginRegistry` — register/unregister/enable/disable/find/lookup by capability.

3 mock plugins: MockAnalyticsPlugin, MockExportPlugin, MockMonitorPlugin.

---

## 5. Built-in Policies (9)

read_only, approval_required, trusted_plugin, sandbox, version_match, dependency_valid, safe_mode, permission_scope, audit_required

---

## 6. Quality Gates

| Gate | Status |
|---|---|
| 0 domain imports | ✅ |
| 0 repository/storage imports | ✅ |
| 0 Conversation/Guardian/Mission modifications | ✅ |
| 0 network/subprocess | ✅ |
| No eval/exec/import string | ✅ |
| Preview only, approval mandatory | ✅ |
| Plugin default read-only | ✅ |
| Frozen DTO, sync only | ✅ |

## 7. Files

| File | Isi |
|---|---|
| `plugin_protocol.py` | Protocol, DTOs |
| `plugin_registry.py` | Registry with enable/disable |
| `plugin_loader.py` | Manifest parser, validator |
| `plugin_policy.py` | 9 built-in policies |
| `plugin_runtime.py` | Runtime pipeline |
| `conversation_plugin.py` | 10 query types |
| `dashboard_plugin.py` | 6 DTO cards |
| `integration_plugin.py` | 3 mock plugins, BasePlugin |

Signature: ZARA 🦋
