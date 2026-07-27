# Workflow Guide

> Cara membuat dan menjalankan workflow di SAM.

## Apa Itu Workflow?

Workflow adalah urutan langkah (step) yang dijalankan secara berurutan. Setiap step memanggil satu **capability** — unit fungsional terkecil di SAM.

## Workflow Sederhana

Workflow paling sederhana adalah daftar capability ID yang dipisahkan koma:

```bash
sam workflow "diagnose-runtime,repair-provider,deploy-workspace"
```

Ini akan:
1. `diagnose-runtime` — memeriksa kesehatan runtime
2. `repair-provider` — memperbaiki provider yang bermasalah
3. `deploy-workspace` — mendeploy workspace

## Workflow Definition (YAML)

Untuk workflow yang lebih kompleks, gunakan file definisi:

```yaml
# examples/diagnose_and_repair.yaml
name: diagnose-and-repair
description: Diagnose runtime and repair if needed
version: "1.0"
steps:
  - id: step1
    capability: diagnose-runtime
    inputs:
      target: "all"
    timeout: 30
    transition:
      on_success: step2
      on_failure: step3

  - id: step2
    capability: deploy-workspace
    inputs:
      workspace: "production"
    timeout: 60

  - id: step3
    capability: repair-provider
    inputs:
      provider: "default"
    timeout: 120
```

Jalankan dengan:

```bash
sam graph run examples/diagnose_and_repair.yaml
```

## Workflow Step Properties

| Properti | Wajib | Deskripsi |
|---|---|---|
| `id` | ✅ | ID unik dalam workflow |
| `capability` | ✅ | ID capability yang akan dijalankan |
| `inputs` | ❌ | Parameter input untuk capability |
| `timeout` | ❌ | Timeout dalam detik |
| `retry` | ❌ | Jumlah percobaan ulang |
| `transition` | ❌ | Aturan transisi antar step |

## Transition Rules

```yaml
transition:
  on_success: next_step_id    # Langkah selanjutnya jika sukses
  on_failure: fallback_step   # Langkah selanjutnya jika gagal
```

## Best Practices

1. **Beri timeout** setiap step — jangan infinite wait
2. **Gunakan retry** untuk step yang tidak deterministik
3. **Dokumentasikan input** yang diperlukan setiap step
4. **Test workflow** dengan `--dry-run` jika tersedia
