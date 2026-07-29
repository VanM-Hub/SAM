# OP-430 — Extension SDK Foundation (Sprint 42)

Dokumentasi arsitektur Extension SDK Foundation untuk Sprint 42.

---

## 1. SDK Architecture

SDK resmi agar pihak ketiga dapat mengembangkan Plugin, Connector, Integration, Adapter, maupun Provider tanpa bergantung pada implementasi internal SAM.

```
SDK → Extension Validator → Compatibility → Conversation → Dashboard
```

**Lokasi kode:** `src/sam/sdk/`

---

## 2. SDK Components

| Modul | Fungsi |
|---|---|
| `sdk_protocol.py` | SDKVersion, SDKMetadata, SDKCapability, SDKContext, SDKResult, SDKCompatibility, SDKProtocol |
| `plugin_sdk.py` | PluginSDK, PluginManifestS, PluginTemplate, PluginValidationS |
| `connector_sdk.py` | ConnectorSDK, ConnectorManifest, ConnectorTemplate, ConnectorValidationS |
| `provider_sdk.py` | ProviderSDK, ProviderManifest, ProviderTemplate, ProviderValidationS |
| `extension_validator.py` | ExtensionValidator, ValidationIssue, CompatibilityReport, ValidationSummary |
| `conversation_sdk.py` | 10 query types |
| `dashboard_sdk.py` | 6 DTO cards |
| `integration_sdk.py` | SDKPipeline |

---

## 3. Extension Lifecycle

```
1. Build manifest (via SDK)
2. Validate manifest (via ExtensionValidator)
3. Check compatibility (SDK version, Python, SAM version)
4. Generate report (CompatibilityReport)
5. Preview (via Pipeline)
6. Deploy (future)
```

---

## 4. SDK Templates

| SDK | Templates |
|---|---|
| PluginSDK | minimal, analytics |
| ConnectorSDK | filesystem, rest_api |
| ProviderSDK | filesystem, http |

Semua template menyertakan manifest example.

---

## 5. Compatibility Model

`ExtensionValidator.check_sdk_compatibility()`:
- SDK version compatibility (<=1.0.0)
- Python version minimum (>=3.8)
- SAM version minimum (>=4.0.0)

---

## 6. Quality Gates

| Gate | Status |
|---|---|
| 0 domain/repo/storage imports | ✅ |
| No Conversation/Guardian/Mission mods | ✅ |
| Frozen DTO, sync only, preview only | ✅ |
| Backward compatible | ✅ |
| SDK provider agnostic | ✅ |

Signature: ZARA 🦋
