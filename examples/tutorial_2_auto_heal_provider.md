# Tutorial 2: Auto-Healing Provider

> Workflow + capability untuk mendeteksi dan memperbaiki provider yang bermasalah.

## Tujuan

Provider yang tidak responsif harus terdeteksi dan diperbaiki secara otomatis.

## Workflow

```yaml
# examples/auto_heal_provider.yaml
name: auto-heal-provider
description: "Detect and repair unhealthy providers"
version: "1.0"
steps:
  - id: detect
    capability: diagnose-runtime
    inputs:
      target: "provider"
    timeout: 30
    transition:
      on_failure: investigate
      on_success: done

  - id: investigate
    capability: diagnose-runtime
    inputs:
      target: "provider"
      detailed: true
    timeout: 60
    transition:
      on_success: decide-action

  - id: decide-action
    capability: decide-action
    inputs:
      based_on: "investigation_result"
    timeout: 10
    transition:
      on_success: repair

  - id: repair
    capability: repair-provider
    timeout: 120
    retry: 2
    transition:
      on_success: verify
      on_failure: escalate

  - id: verify
    capability: diagnose-runtime
    inputs:
      target: "provider"
    timeout: 30
    transition:
      on_failure: repair  # Loop repair jika masih gagal
      on_success: done

  - id: escalate
    capability: send-alert
    inputs:
      channel: "admin"
      message: "Provider auto-heal failed after retries"

  - id: done
    capability: log-event
    inputs:
      message: "Provider health OK"
```

## Output yang Diharapkan

```
Workflow: auto-heal-provider
  Step 1: detect → success (provider OK)
  Step 2: (skipped)
Verdict: No action needed
```

Atau jika ada masalah:

```
Workflow: auto-heal-provider
  Step 1: detect → error (provider unhealthy)
  Step 2: investigate → success
  Step 3: decide-action → success (repair needed)
  Step 4: repair → success
  Step 5: verify → success (provider OK now)
  Step 8: done → success
Verdict: Provider auto-healed successfully
```
