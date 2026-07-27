# Tutorial 1: Monitoring OpenClaw

> Workflow untuk memonitor health OpenClaw secara periodik.

## Tujuan

Buat workflow yang memeriksa health OpenClaw setiap 5 menit dan mengirim alert jika ada masalah.

## Workflow

```yaml
# examples/monitor_openclaw.yaml
name: monitor-openclaw
description: "Periodic health check for OpenClaw"
steps:
  - id: check-health
    capability: diagnose-runtime
    inputs:
      target: "openclaw"
    timeout: 30
    transition:
      on_failure: send-alert

  - id: send-alert
    capability: send-alert
    inputs:
      channel: "admin"
      message: "OpenClaw health check failed"
```

## Menjalankan

```bash
# Manual
sam graph run examples/monitor_openclaw.yaml

# Periodik (via scheduler jika tersedia)
sam workflow "diagnose-runtime,send-alert" --interval 300
```

## Output yang Diharapkan

```
Workflow: monitor-openclaw
  Step 1: check-health → success
  Step 2: (skipped — no failure)
```

Atau jika gagal:

```
Workflow: monitor-openclaw
  Step 1: check-health → error
  Step 2: send-alert → success (alert sent)
```
