# Layer Validation

## Layer Model

```
Presentation         (CLI, Desktop, API, Hosting)
     |
     v
Conversation Layer   (bridges — request/response)
     |
     v
Runtime Layer        (Guardian, Decision, Approval, Activation, Execution, Runtime Kernel)
     |
     v
Coordinator Layer    (Runtime Kernel, Bridge Router, Orchestrator)
     |
     v
Domain DTO Layer     (frozen dataclasses — flow between subsystems)
     |
     v
Infrastructure Layer (adapter, plugin, provider, persistence)
```

## Layer Rules

1. **Top layer** can depend on any layer below
2. **Bottom layer** cannot depend on any layer above
3. **Conversation bridges** only transform DTOs — no business logic
4. **Runtime subsystems** only interact via DTOs — no direct method calls across runtimes
5. **DTO layer** has zero dependencies on runtime/coordination layers
6. **Infrastructure** provides abstractions — never calls runtime directly

## Violation Check

| Check | Status |
|-------|--------|
| Presentation depends on runtime? | ✅ (authorized) |
| Conversation depends on infrastructure? | ✅ (authorized) |
| Runtime depends on DTO layer? | ✅ (authorized) |
| DTO depends on infrastructure? | ✅ (none do) |
| Infrastructure depends on runtime? | ✅ (none do) |
| Cross-runtime direct method call? | ✅ (none — all via bridges) |
| Import from higher layer to lower? | ✅ (no violations detected) |

## Layer Integrity

**Layers are clean.** No layer violation detected.
Architecture follows strict top-down dependency.
