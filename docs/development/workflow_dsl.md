# Workflow DSL

> Panduan menulis workflow dengan Domain Specific Language (DSL) SAM.

## Format Workflow

Workflow didefinisikan dalam file YAML dengan struktur berikut:

```yaml
name: workflow-name              # Nama workflow (wajib)
description: "Deskripsi"         # Deskripsi (opsional)
version: "1.0"                   # Versi (opsional, default "1.0.0")
steps:                           # Daftar langkah (wajib, minimal 1)
  - id: step1                    # ID unik (wajib)
    capability: cap-id           # ID capability (wajib)
    inputs:                      # Input untuk capability (opsional)
      key: value
    timeout: 30                  # Timeout detik (opsional)
    retry: 3                     # Retry count (opsional)
    transition:                  # Aturan transisi (opsional)
      on_success: step2
      on_failure: step3
```

## Workflow Dasar

```yaml
# simple_workflow.yaml
name: hello-world
steps:
  - id: greet
    capability: greeter
    inputs:
      name: "SAM"
```

## Workflow dengan Transisi

```yaml
name: diagnose-and-repair
steps:
  - id: diagnose
    capability: diagnose-runtime
    timeout: 30
    transition:
      on_success: deploy
      on_failure: repair

  - id: repair
    capability: repair-provider
    timeout: 120
    retry: 2
    transition:
      on_success: deploy
      on_failure: notify

  - id: deploy
    capability: deploy-workspace
    timeout: 60

  - id: notify
    capability: send-alert
    inputs:
      message: "Repair failed after retries"
```

## Workflow Parallel

```yaml
name: parallel-check
steps:
  - id: check-cpu
    capability: check-cpu
    timeout: 10

  - id: check-memory
    capability: check-memory
    timeout: 10

  - id: check-disk
    capability: check-disk
    timeout: 10

  - id: aggregate
    capability: aggregate-results
    inputs:
      sources: ["check-cpu", "check-memory", "check-disk"]
```

## Workflow dengan Retry

```yaml
name: retry-example
steps:
  - id: flaky-operation
    capability: flaky-capability
    timeout: 30
    retry: 3
    transition:
      on_success: done
      on_failure: fallback

  - id: fallback
    capability: fallback-capability
    timeout: 30

  - id: done
    capability: notify-done
```

## Validasi Workflow

SAM akan memvalidasi workflow sebelum eksekusi:

- ✅ Semua step memiliki `id` unik
- ✅ Semua `capability` terdaftar
- ✅ Transisi mengarah ke step yang valid
- ❌ Circular dependency ditolak
- ❌ Step tanpa transisi `on_success` akan dianggap final

## Contoh Lengkap

Lihat juga:
- [Workflow Guide](../user/workflow_guide.md) — panduan pengguna
- [Tutorial & Contoh](#) — contoh workflow siap pakai
