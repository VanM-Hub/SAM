# Pipeline Specification

Auto-generated — Architecture Freeze v10.

---

## 1. Guardian Live Pipeline

### Purpose
Monitor, assess, and triage runtime state changes into decisions.

### Input
- `GuardianEvent` — raw events from observed state
- `RuntimeSnapshot` — periodic runtime state snapshots

### Stages

| Stage | Module | Processing | Output DTO |
|-------|--------|-----------|------------|
| 1. Event | `event.py` | Capture and classify by type/source | `GuardianEvent` |
| 2. State | `state.py`, `registry.py` | Current runtime state + registry | `RuntimeState`, `RuntimeSnapshot` |
| 3. Sync | `synchronizer.py`, `validator.py` | Synchronize + validate consistency | SyncReport |
| 4. Transition | `transition.py`, `diff_engine.py`, `change_detector.py` | Detect changes, diff snapshots | `RuntimeTransition`, `DiffResult` |
| 5. Situation | `situation.py`, `correlator.py`, `classifier.py` | Correlate and classify | `GuardianSituation`, `SituationSnapshot` |
| 6. Assessment | `assessment.py`, `risk_assessment.py`, `priority_assessment.py` | Assess risk + priority | `GuardianAssessment`, `AssessmentSnapshot` |
| 7. Intent | `intent.py`, `intent_builder.py`, `intent_policy.py` | Formulate intent | `GuardianIntent` |
| 8. Decision Input | `decision_input.py`, `handoff.py`, `eligibility.py` | Hand off to decision | `DecisionInput`, `DecisionCandidate` |

### Output
- `DecisionInput` — ready for Decision Runtime processing

### Entry Point
- `GuardianLiveRuntime.start()` via `runtime.py`

### Exit Point
- `HandoffEngine.handoff()` pushes to Decision Queue

### Immutable DTOs
- All data classes are `frozen=True`
- No state mutation after construction

---

## 2. Decision Runtime Pipeline

### Purpose
Process guardian output into actionable decisions via evaluation, planning, approval, certification, and finalization.

### Input
- `DecisionInput` (from Guardian)
- `DecisionCandidate` (from Guardian)

### Stages

| Stage | Module | Processing | Output DTO |
|-------|--------|-----------|------------|
| 1. Evaluation | `evaluation.py` | Evaluate decision eligibility | EvaluationResult |
| 2. Planning | `planning.py`, `planner.py`, `planning_alternatives.py` | Generate alternatives | DecisionPlan |
| 3. Approval | `approval_activation.py` -> `approval_session.py` -> `approval_gateway.py` | Multi-level approval | ApprovalVerdict |
| 4. Certification | `certification_engine.py` | Certify compliance | CertificationResult |
| 5. Finalization | `finalization.py`, `finalization_engine.py` | Finalize and package | FinalizationSummary |

### Output
- `CertificationVerdict` / `FinalizationSummary` — ready for Activation Runtime

### Entry Point
- `operations.brain.decision.runtime_v3` — `DecisionRuntime`

### Exit Point
- `FinalizationEngine.finalize()` — activates next subsystem

---

## 3. Approval Runtime Pipeline

### Purpose
Multi-level approval with policy enforcement, history, delegation, and audit.

### Input
- Approval request (from Decision Runtime or conversation)
- `PolicyEngine` rules

### Stages

| Stage | Module | Processing | Output DTO |
|-------|--------|-----------|------------|
| 1. Intake | `intake_record.py`, `intake_registry.py`, `intake_validator.py` | Validate and register request | IntakeRecord |
| 2. Policy | `policy.py`, `policy_engine.py`, `policy_builder.py` | Apply policy rules | PolicyVerdict |
| 3. Workflow | `workflow.py`, `workflow_engine.py`, `workflow_rules.py` | Route through workflow | WorkflowInstance |
| 4. Multilevel | `multilevel.py`, `multilevel_engine.py` | Chain of approvals | MultilevelResult |
| 5. History | `history.py`, `history_engine.py` | Record approval history | ApprovalHistory |
| 6. Dashboard | `dashboard_*.py` | UI bridges | DashboardCards |

---

## 4. Operational Brain Pipeline

### Purpose
Plan, schedule, monitor, and report operational health.

### Input
- Operational goals
- System health data

### Stages

| Stage | Module | Processing | Output |
|-------|--------|-----------|--------|
| 1. Health | `health_aggregator.py` | Aggregate health | HealthReport |
| 2. Readiness | `readiness_checker.py` | Check readiness | ReadinessReport |
| 3. Planning | `operational_planner.py`, `operational_planning.py` | Create operational plan | OperationalPlan |
| 4. Scheduling | `operational_scheduler.py` | Schedule tasks | OperationalSchedule |
| 5. Monitoring | `operational_monitor.py`, `operational_metrics.py` | Monitor execution | OperationalMetrics |
| 6. Export | `operational_plan_exporter.py` | Export plan | PlanExport |

---

## 5. Activation Runtime Pipeline

### Purpose
Transform approved decisions into executable activation packages.

### Input
- Approved decision (from Decision/Approval)
- Activation context

### Stages

| Stage | Module | Processing | Output |
|-------|--------|-----------|--------|
| 1. Request | `activation_request.py` | Create activation request | ActivationRequest |
| 2. Builder | `activation_builder.py` | Build activation candidate | ActivationCandidate |
| 3. Draft | `activation_draft.py` | Draft activation package | ActivationDraft |
| 4. Package | `activation_package.py` -> `package_builder.py` | Build final package | ActivationPackage |
| 5. Validation | `activation_validator.py`, `package_validator.py` | Validate package | PackageValidationResult |
| 6. Export | `package_export.py`, `package_registry.py` | Export to registry | PackageExport |

---

## 6. Execution Runtime Pipeline

### Purpose
Plan, execute, monitor, and validate execution of activation packages.

### Input
- `ActivationPackage` (from Activation Runtime)

### Stages

| Stage | Module | Processing | Output |
|-------|--------|-----------|--------|
| 1. Request | `execution_request.py` | Parse execution request | ExecutionRequest |
| 2. Strategy | `execution_strategy.py`, `execution_validator.py` | Strategy + validation | ExecutionStrategy |
| 3. Resource | `resource_plan.py`, `resource_allocator.py` | Allocate resources | ResourcePlan |
| 4. Dependency | `dependency_graph.py`, `dependency_resolver.py` | Resolve dependencies | DependencyGraph |
| 5. Timeline | `timeline.py`, `timeline_builder.py` | Build timeline | ExecutionTimeline |
| 6. Budget | `budget.py`, `budget_engine.py` | Allocate budget | BudgetAllocation |
| 7. Risk | `risk.py`, `risk_engine.py` | Assess risk | RiskAssessment |
| 8. Quality | `quality.py`, `quality_engine.py` | Quality check | QualityResult |
| 9. Simulation | `simulation.py`, `simulation_engine.py` | Simulate execution | SimulationResult |
| 10. Assembly | `assembly.py`, `assembly_engine.py` | Assemble execution | ExecutionAssembly |

---

## 7. Runtime Kernel Pipeline

### Purpose
Central coordination layer — orchestrates all subsystems through bridges.

### Input
- System boot signal
- Coordinator plan

### Stages

| Stage | Module | Processing | Output |
|-------|--------|-----------|--------|
| 1. Boot | `startup_manager.py` | 6-phase startup | StartupReport |
| 2. Context | `runtime_context.py`, `runtime_configuration.py` | Build runtime context | RuntimeContext |
| 3. Registry | `runtime_registry.py`, `runtime_catalog.py` | Discover all runtimes | RuntimeCatalog |
| 4. State | `state_machine.py`, `state_snapshot.py` | Initialize FSM | RuntimeState |
| 5. Lifecycle | `lifecycle_manager.py` | Manage lifecycle | LifecycleState |
| 6. Bridge | `adapter_registry.py`, `bridge_router.py`, `transform_engine.py` | Connect subsystems | BridgeRegistry |
| 7. Health | `health_checker.py`, `health_engine.py` | Health check | HealthReport |
| 8. Security | `security_manager.py`, `access_controller.py` | Access control | SecurityVerdict |
| 9. Scheduler | `scheduler_engine.py`, `task_scheduler.py` | Schedule tasks | SchedulePlan |
| 10. Event Bus | `event_bus.py`, `event_dispatcher.py` | Publish/subscribe | EventBusInstance |
| 11. Coordinator | `coordination_engine.py`, `orchestrator.py` | Coordinate tasks | CoordinationPlan |
| 12. Telemetry | `telemetry_collector.py`, `metrics_aggregator.py` | Collect metrics | TelemetryReport |
| 13. Final | `kernel_final.py`, `final_inspector.py` | 11-component check | FinalVerdict |

---
