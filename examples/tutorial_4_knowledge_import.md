# Tutorial 4: Knowledge Import

> Mengimpor knowledge dari file YAML ke Knowledge Graph.

## Tujuan

Impor data knowledge dari file YAML ke dalam SAM Knowledge Graph untuk digunakan oleh capability dan workflow.

## Format File Knowledge

```yaml
# examples/knowledge/patterns.yaml
knowledge:
  - id: pattern-high-cpu
    type: pattern
    title: "High CPU Detection"
    description: "Detect when CPU usage exceeds threshold"
    tags: ["cpu", "performance", "monitoring"]
    content:
      metric: "cpu_percent"
      threshold: 80
      window: "5m"
      severity: "warning"
    source: "operations-team"

  - id: rule-auto-scale
    type: rule
    title: "Auto Scale Rule"
    description: "Automatically scale when memory > 90%"
    tags: ["scaling", "memory", "autonomous"]
    content:
      trigger: "memory_percent > 90"
      action: "scale_up"
      cooldown: "300s"
    source: "architecture-team"
```

## Workflow Import

```yaml
# examples/import_knowledge.yaml
name: import-knowledge
description: "Import knowledge from YAML file"
steps:
  - id: load-file
    capability: load-knowledge-file
    inputs:
      path: "examples/knowledge/patterns.yaml"
    timeout: 30
    transition:
      on_failure: report-error

  - id: validate
    capability: validate-knowledge
    inputs:
      source: "load-file"
    timeout: 30
    transition:
      on_failure: report-error

  - id: import
    capability: import-to-graph
    inputs:
      knowledge: "${validate}"
    timeout: 60
    transition:
      on_failure: report-error

  - id: verify
    capability: query-knowledge
    inputs:
      query: "pattern-high-cpu"
    timeout: 10
    transition:
      on_failure: report-error

  - id: report-error
    capability: send-alert
    inputs:
      channel: "admin"
      message: "Knowledge import failed"

  - id: report-success
    capability: log-event
    inputs:
      message: "Knowledge imported successfully"
```

## Menjalankan

```bash
# Import knowledge
sam graph run examples/import_knowledge.yaml

# Verifikasi langsung
sam run query-knowledge --inputs '{"query": "pattern-high-cpu"}'
```

## Output yang Diharapkan

```
Knowledge import: success
  Items imported: 2
  Items skipped: 0
  Duration: 0.5s
```

## Knowledge Categories

| Tipe | Deskripsi | Contoh |
|---|---|---|
| `pattern` | Pola masalah | High CPU, Memory leak, Disk full |
| `rule` | Aturan bisnis | Auto scale, Restart policy |
| `template` | Template workflow | Monitoring, Backup, Deploy |
| `reference` | Referensi | API docs, Konfigurasi |
| `lesson` | Pelajaran | Root cause analysis, Postmortem |
