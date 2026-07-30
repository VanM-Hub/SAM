# Entry Point Audit

Auto-generated — Architecture Freeze v10.

---

## Audit Result: Single Official Entry

| Entry Point | Path | Type | Status |
|------------|------|------|--------|
| **Official** | `src/sam/launcher/` | Module | ✅ PRIMARY |
| CLI | `src/sam/cli/` | Subcommand | ✅ Secondary |
| Desktop | `src/sam/desktop/` | Qt GUI | ✅ Secondary |
| API | `src/sam/api/` | HTTP | ⚠️ Preview |
| Hosting | `src/sam/hosting/` | Service | ✅ Secondary |
| Run script | `run.py` | Runner | ✅ Convenience |

### Official Entry Point: `sam.launcher`

```python
# From pyproject.toml:
[project.scripts]
sam = "sam.launcher.cli_entry:main"
```

Tiga mode boot:
1. **CLI** — `sam [command] [args]` — via `sam.launcher.cli_entry`
2. **Desktop** — `sam desktop` — via `sam.launcher.application`
3. **Host** — `sam host` — via `sam.launcher.host_launcher`

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
| All entry points route through launcher | ✅ |
| No direct file execution bypass | ✅ (no if __name__ == "__main__" outside launcher) |
| Consistent CLI interface | ✅ (typer-based) |
| Desktop launcher is optional (no Qt = no desktop) | ✅ |
| Host launcher available for non-interactive | ✅ |

### Recommendation

Single official entry: `python -m sam.launcher` atau `sam [command]`.
Tidak ada perubahan diperlukan.
