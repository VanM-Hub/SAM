# Entry Point Audit

Auto-generated — Architecture Freeze v10.

---

## Audit Result: Single Official Entry

| Entry Point | Path | Type | Status |
|------------|------|------|--------|
| **Official** | `src/sam/launcher/` | Module | LULUS PRIMARY |
| CLI | `src/sam/cli/` | Subcommand | LULUS Secondary |
| Conversation Host | `src/sam/presentation/conversation/` | Presentation | LULUS Active (Program G) |
| Dashboard Host | `src/sam/presentation/dashboard/` | Presentation | LULUS Active (Program H) |
| CLI Host | `src/sam/presentation/cli/` | Presentation | LULUS Active (Program I) |
| REST API | `src/sam/api/` | HTTP | LULUS Active (Program J) |
| LLM Wiring | `src/sam/api/llm_wiring.py` | Composition root | LULUS Active (Program K) |
| Hosting | `src/sam/hosting/` | Service | LULUS Secondary |
| Run script | `run.py` | Runner | LULUS Convenience |

### Official Entry Point: `sam.launcher`

```python
# From pyproject.toml:
[project.scripts]
sam = "sam.launcher.cli_entry:main"
```

Lima entry point script (Program I, `sam.launcher.cli_entry`):
1. **`sam`** - host auto (deteksi `SAM_HOST` / console)
2. **`sam-console`** - mode console
3. **`sam-desktop`** - mode desktop (butuh Qt)
4. **`sam-headless`** - mode headless
5. **`sam-diagnostic`** - diagnostik lalu keluar

Presentation hosts (Program G-K) semuanya berjalan melalui `runtime_service.api`;
host composition root tidak mengimpor Runtime/Registry/Provider/Connector/
ExecutionRuntime secara langsung.

### Launcher Pipeline

```
CLI Args
  |
  v
ConfigLoader -> Environment -> PluginDiscovery
  |
  v
RuntimeBootstrap -> StartupPipeline -> StartupReport
  |
  v
RuntimeRegistry -> Diagnostics -> RecoveryStartup
  |
  v
Integration -> HostManager
  |
  v
Runtime State: ACTIVE
```

### Entry Point Validation

| Check | Result |
|-------|--------|
| All entry points route through launcher | LULUS |
| No direct file execution bypass | LULUS (no if __name__ == "__main__" outside launcher) |
| Consistent CLI interface | LULUS (launcher CLI: 5 entry points) |
| Desktop launcher is optional (no Qt = no desktop) | LULUS |
| Host launcher available for non-interactive | LULUS |
| Presentation hosts (G-K) via runtime_service.api, 0 bypass | LULUS (compliance Program K)

### Recommendation

Single official entry: `python -m sam.launcher` atau `sam` (5 entry points).
Tidak ada perubahan arsitektur diperlukan; status presentasi & aktivasi LLM
dicatat di Entry_Points.md atas dan panduan user (REST: rest_api_guide.md;
LLM: llm_integration_guide.md).
