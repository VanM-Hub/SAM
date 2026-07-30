# Public API Inventory

Auto-generated from `src/sam/` — 38708 Python files.

## `sam.activation`

**Exported (72):**
- `ActivationContext`
- `ActivationRequest`
- `ActivationCandidate`
- `ActivationRegistry`
- `ActivationSnapshot`
- `ActivationBuilder`
- `ActivationDraft`
- `ActivationValidator`
- `ValidationReport`
- `ValidationError`
- `ActivationRules`
- `ActivationRule`
- `ActivationConstraints`
- `ConstraintResult`
- `ActivationReadiness`
- `ReadinessCheck`
- `ActivationReport`
- `ActivationReportBuilder`
- `ActivationStrategyEngine`
- `ActivationStrategy`
- `AlternativeGenerator`
- `ActivationAlternative`
- `ActivationPriority`
- `PriorityAssignment`
- `ActivationWindowManager`
- `ActivationWindow`
- `SequenceBuilder`
- `ActivationSequence`
- `ActivationStep`
- `ActivationPackage`
- `PackageBuilder`
- `PackageValidator`
- `PackageValidation`
- `PackageRegistry`
- `PackageExporter`
- `PackageExport`
- `ActivationMetricsCollector`
- `ActivationMetrics`
- `ActivationMonitor`
- `MonitorEvent`
- `ActivationHistory`
- `HistoryEntry`
- `ActivationSnapshotState`
- `ActivationHealthChecker`
- `ActivationHealthReport`
- `ActivationRuntimeEngine`
- `RuntimeStatus`
- `ActivationPipeline`
- `ActivationCoordinator`
- `RuntimeReport`
- `RuntimeReportBuilder`
- `ActivationRuntimeStatus`
- `ActivationRuntimeStatusBuilder`
- `ConversationActivation`
- `ConversationValidation`
- `ConversationStrategy`
- `ConversationPackage`
- `ConversationMonitor`
- `ConversationRuntime`
- `DashboardActivation`
- `ActivationCard`
- `DashboardValidation`
- `ValidationCard`
- `DashboardStrategy`
- `StrategyCard`
- `DashboardPackage`
- `PackageCard`
- `DashboardMonitor`
- `MonitorCard`
- `DashboardRuntime`
- `RuntimeCard`
- `ActivationRuntime`

## `sam.api`

*No public exports defined.*

### `api/routes` — imports only

## `sam.approval`

**Imports (46):**
- `from .intake_record import ApprovalIntakeRecord, IntakeMetadata, IntakeSource`
- `from .intake_validator import IntakeValidator, ValidationResult`
- `from .intake_normalizer import IntakeNormalizer, NormalizedApprovalRecord`
- `from .intake_registry import IntakeRegistry`
- `from .intake_summary import IntakeSummaryBuilder, ApprovalIntakeSummary`
- `from .conversation_intake import ConversationIntakeBridge`
- `from .dashboard_intake import DashboardIntakeBridge`
- `from .workflow import ApprovalWorkflow, WorkflowPhase, WorkflowTransition, PHASE_TRANSITIONS`
- `from .workflow_engine import WorkflowEngine, WorkflowTransitionError`
- `from .workflow_builder import WorkflowBuilder`
- `from .workflow_rules import WorkflowRules`
- `from .conversation_workflow import ConversationWorkflowBridge`
- `from .dashboard_workflow import DashboardWorkflowBridge`
- `from .policy import ApprovalPolicy, PolicyEffect, PolicyCondition, PolicyEvaluationResult`
- `from .policy_engine import PolicyEngine`
- `from .policy_builder import PolicyBuilder`
- `from .policy_validator import PolicyValidator`
- `from .conversation_policy import ConversationPolicyBridge`
- `from .dashboard_policy import DashboardPolicyBridge`
- `from .multilevel import ApprovalLevel, MultiLevelApproval`
- *... and 26 more*

## `sam.autonomous`

**Exported (10):**
- `AutonomousAction`
- `AutonomousActionStatus`
- `ActionType`
- `RiskLevel`
- `ApprovalRequest`
- `ActionExecutor`
- `SafetyPolicy`
- `ApprovalManager`
- `AutoRecovery`
- `PluginIsolation`

## `sam.autonomy`

**Exported (13):**
- `AssessmentResult`
- `AutonomyConfig`
- `AutonomyController`
- `AutonomyLevel`
- `EscalationManager`
- `EscalationRequest`
- `GracefulDegradation`
- `GuardrailResult`
- `GuardrailRule`
- `Guardrails`
- `SafetyBoundary`
- `SafetyEnvelope`
- `SelfAssessment`

## `sam.cli`

*No public exports defined.*

## `sam.cluster`

**Exported (9):**
- `ClusterCognitiveState`
- `ClusterCognitiveStateManager`
- `ClusterKnowledgeShare`
- `ClusterStrategySync`
- `Insight`
- `InsightBroker`
- `LearningAggregator`
- `SharedKnowledge`
- `StrategyProposal`

## `sam.cognition`

**Exported (19):**
- `ArbitrationResult`
- `AttentionManager`
- `AttentionProfile`
- `CognitiveManager`
- `CognitiveSession`
- `CognitiveSessionManager`
- `CognitiveState`
- `CognitiveStateManager`
- `ContextItem`
- `ContextWindow`
- `FocusArea`
- `GoalArbitrator`
- `GoalRequest`
- `GoalType`
- `SESSION_ABANDONED`
- `SESSION_ACTIVE`
- `SESSION_COMPLETED`
- `WorkingMemory`
- `WorkingMemoryManager`

## `sam.cognitive`

**Exported (26):**
- `# Fase 1
    "Goal`
- `GoalStatus`
- `GoalTree`
- `GoalTreeManager`
- `# Fase 2
    "AutonomyLevel`
- `AutonomyConfig`
- `CognitiveBudget`
- `BudgetTracker`
- `BUDGET_REASONING`
- `BUDGET_PLANNING`
- `BUDGET_REVISION`
- `BUDGET_LEARNING`
- `ALL_BUDGET_TYPES`
- `# Fase 3
    "HealingStrategy`
- `HealingAction`
- `HealingResult`
- `HealingManager`
- `PATTERN_PROVIDER_TIMEOUT`
- `PATTERN_WORKSPACE_CORRUPTION`
- `PATTERN_MEMORY_LEAK`
- `PATTERN_ERROR_SPIKE`
- `PATTERN_LATENCY_INCREASE`
- `ALL_BUILTIN_PATTERNS`
- `DegradationLevel`
- `DegradationRecord`
- `DegradationManager`

## `sam.collaboration`

**Exported (14):**
- `Agent`
- `AGENT_STATUSES`
- `AgentRegistry`
- `Message`
- `MessageType`
- `MessagePriority`
- `MESSAGE_STATUSES`
- `AgentProtocol`
- `DelegationStatus`
- `DelegationRequest`
- `DelegationManager`
- `CollaborationWorkflow`
- `CollaborationWorkflowManager`
- `WORKFLOW_STATUSES`

## `sam.confidence`

**Exported (2):**
- `OperationalConfidenceCalculator`
- `ConfidenceBreakdown`

## `sam.contracts`

**Exported (5):**
- `Mission`
- `MissionStatus`
- `Objective`
- `DesiredOperationalState`
- `RuntimeState`

## `sam.core`

**Exported (39):**
- `RuntimeDaemon`
- `DaemonConfig`
- `RuntimeService`
- `ServiceManager`
- `ServiceHealth`
- `HealthStatus`
- `TimeProvider`
- `SystemClock`
- `FrozenClock`
- `VirtualClock`
- `EventBus`
- `Event`
- `Job`
- `JobType`
- `JobRecord`
- `JobStatus`
- `JobQueue`
- `Scheduler`
- `Notification`
- `NotificationSeverity`
- `NotificationService`
- `StateStore`
- `StateRecord`
- `StateType`
- `StateSavedEvent`
- `StateDeletedEvent`
- `StateStoreError`
- `OptimisticLockError`
- `RuntimeResource`
- `ResourceType`
- `ResourceStatus`
- `ResourceOwner`
- `ResourceError`
- `ResourceNotFoundError`
- `ResourceVersionConflictError`
- `ResourceNotOwnedError`
- `ResourceOwnershipConflictError`
- `ResourceManager`
- `ResourceDirectory`

## `sam.desktop`

**Exported (2):**
- `HomePage`
- `run`

### `desktop/pages` — 8 exports

## `sam.dos`

**Exported (2):**
- `DOSModel`
- `DOSLoader`

## `sam.events`

**Exported (2):**
- `EventBus`
- `Event`

## `sam.evidence`

**Exported (4):**
- `Evidence`
- `EvidenceType`
- `EvidenceStatus`
- `EvidenceStore`

## `sam.evolution`

**Exported (11):**
- `OptimizableParam`
- `ParamManager`
- `PARAM_CATEGORIES`
- `SelfOptimizer`
- `OptimizationSuggestion`
- `OptimizationGoal`
- `EvolutionPolicy`
- `EvolutionProposal`
- `ProposalType`
- `ProposalStatus`
- `PolicyRule`

## `sam.execution`

*No public exports defined.*

### `execution/adapters` — imports only

### `execution/connectors` — imports only

### `execution/dispatch` — imports only

### `execution/engine` — imports only

### `execution/providers` — imports only

### `execution/runtime` — imports only

## `sam.federation`

**Exported (16):**
- `ClusterTrust`
- `ConflictResolver`
- `ConflictResult`
- `ConsensusEngine`
- `ConsensusVote`
- `FederationManager`
- `FederationMessage`
- `FederationProtocol`
- `KnowledgeOffer`
- `KnowledgeRequest`
- `Provenance`
- `ProvenanceManager`
- `SharingPolicy`
- `SovereigntyManager`
- `SovereigntyPolicy`
- `TrustManager`

## `sam.guardian`

**Exported (8):**
- `ObserverEngine`
- `AnalyzerEngine`
- `DecisionEngine`
- `GuardianDecision`
- `PolicyEngine`
- `ActionEngine`
- `VerificationEngine`
- `GuardianPipeline`

### `guardian/live` — 180 exports

## `sam.healing`

**Exported (3):**
- `ReflectionRecord`
- `ReflectionManager`
- `SelfHealingLoop`

## `sam.hosting`

**Exported (3):**
- `HostingAdapter`
- `DesktopAdapter`
- `DockerAdapter`

## `sam.institutional`

**Exported (7):**
- `InstitutionalMemory`
- `InstitutionalMemoryManager`
- `MEMORY_TYPES`
- `Lesson`
- `LessonManager`
- `TemplateEvolution`
- `TemplateEvolutionManager`

## `sam.integration`

*No public exports defined.*

## `sam.intelligence`

**Exported (8):**
- `Incident`
- `IncidentSeverity`
- `RootCause`
- `Recommendation`
- `IncidentDetector`
- `RootCauseAnalyzer`
- `Recommender`
- `KnowledgeLookup`

## `sam.knowledge`

**Exported (9):**
- `KnowledgeDocument`
- `KnowledgeRelationship`
- `KnowledgeFact`
- `KnowledgeHistory`
- `KnowledgeLoader`
- `KnowledgeStore`
- `create_knowledge_store`
- `KnowledgeGraph`
- `create_knowledge_graph`

## `sam.language`

**Exported (4):**
- `humanize`
- `humanize_event_message`
- `INTERNAL_TO_HUMAN`
- `HumanActivityCategory`

## `sam.launcher`

*No public exports defined.*

## `sam.mission`

**Exported (2):**
- `MissionModel`
- `MissionLoader`

## `sam.models`

**Exported (13):**
- `Entity`
- `Capability`
- `Workflow`
- `Execution`
- `Evidence`
- `AuditEvent`
- `Knowledge`
- `Pattern`
- `Recommendation`
- `ReasoningTrace`
- `MemoryRecord`
- `CapabilityDescriptor`
- `CorrelationContext`

## `sam.openclaw`

**Exported (7):**
- `OpenClawStatus`
- `OpenClawComponent`
- `OpenClawHealth`
- `OpenClawWorkspace`
- `OpenClawDiscovery`
- `OpenClawHealthCollector`
- `OpenClawLogAnalyzer`

## `sam.operational_brain`

**Exported (49):**
- `OperationalContext`
- `GoalType`
- `OperationalGoal`
- `OperationalCandidate`
- `OperationalRegistry`
- `OperationalSnapshot`
- `OperationalBuilder`
- `PriorityTier`
- `PlanEntry`
- `PlanSummary`
- `OperationalPrioritizer`
- `OperationalPlanner`
- `OperationalPlanning`
- `ScheduledItem`
- `Schedule`
- `OperationalScheduler`
- `OperationalPlan`
- `PlanDocument`
- `OperationalPlanExporter`
- `OperationalMetrics`
- `MetricsCollector`
- `CycleSnapshot`
- `OperationalMonitor`
- `HealthReport`
- `HealthAggregator`
- `DependencyNode`
- `DependencyGraph`
- `CycleError`
- `DependencyResolver`
- `ReadinessStatus`
- `ReadinessCheck`
- `ReadinessReport`
- `ReadinessChecker`
- `OperationalConversation`
- `ConversationPlanning`
- `ConversationScheduling`
- `ConversationPlanExport`
- `ConversationReadiness`
- `ConversationMonitor`
- `OperationalDashboardCard`
- `OperationalDashboard`
- `PlanningCard`
- `DashboardPlanning`
- `SchedulingCard`
- `DashboardScheduling`
- `PlanExportCard`
- `DashboardPlanExport`
- `ReadinessCard`
- `DashboardReadiness`

## `sam.operations`

**Imports (1):**
- `from . import brain  # noqa: F401 — Sprint 19 Operational Brain Foundation`

### `operations/brain` — 97 exports

### `operations/engine` — 1 exports

### `operations/models` — imports only

### `operations/orchestrator` — 31 exports

### `operations/presentation` — 64 exports

### `operations/providers` — imports only

### `operations/rca` — 3 exports

### `operations/reasoning` — 23 exports

### `operations/brain/decision` — imports only

### `operations/brain/guardian` — 120 exports

### `operations/brain/learning` — imports only

### `operations/brain/reasoning` — imports only

### `operations/presentation/console` — 57 exports

### `operations/presentation/desktop` — 16 exports

### `operations/presentation/desktop/qt` — 39 exports

## `sam.patterns`

**Exported (4):**
- `PatternDetection`
- `PatternRule`
- `PatternSeverity`
- `PatternEngine`

## `sam.persistence`

**Exported (8):**
- `Database`
- `EvidenceRepository`
- `KnowledgeRepository`
- `PatternRepository`
- `RecommendationRepository`
- `ApprovalRepository`
- `WorkflowStateRepository`
- `ScheduleRepository`

### `persistence/migrations` — 1 exports

## `sam.plugin`

**Exported (19):**
- `PluginManifest`
- `PluginPermission`
- `PluginStatus`
- `PluginManifestLoader`
- `PluginManifestValidator`
- `PluginRegistry`
- `PluginDescriptor`
- `PersistentPluginRegistry`
- `create_plugin_registry`
- `PluginRepository`
- `PluginDiscovery`
- `create_plugin_discovery`
- `PluginLifecycleManager`
- `DependencyResolver`
- `parse_version_constraint`
- `satisfies`
- `satisfies_all`
- `PluginHealthChecker`
- `PluginHealthStatus`

## `sam.plugins`

*No public exports defined.*

## `sam.reasoning`

**Exported (18):**
- `Intent`
- `IntentType`
- `IntentStatus`
- `IntentParser`
- `GraphTemplate`
- `BUILTIN_TEMPLATES`
- `get_default_template`
- `PlanningEngine`
- `PlanError`
- `ReasoningEngine`
- `ReasoningResult`
- `PlanCandidate`
- `PlanRanker`
- `GraphRevision`
- `RevisionManager`
- `RevisionTrigger`
- `IntentEvolution`
- `EvolutionManager`

## `sam.recommendations`

**Exported (4):**
- `Recommendation`
- `RecommendationSeverity`
- `RecommendationStatus`
- `RecommendationEngine`

## `sam.render`

**Exported (3):**
- `CLIRenderer`
- `DesktopRenderer`
- `JSONRenderer`

## `sam.reporting`

**Exported (3):**
- `ExecutionReport`
- `ReportSummary`
- `ReportGenerator`

## `sam.runtime`

**Exported (6):**
- `RuntimeState`
- `RuntimeCoordinator`
- `BootstrapManager`
- `SessionManager`
- `ShutdownManager`
- `RecoveryManager`

## `sam.runtime_kernel`

**Imports (68):**
- `from sam.runtime_kernel.runtime_context import (`
- `from sam.runtime_kernel.runtime_identity import IdentityBuilder, EnvironmentBuilder`
- `from sam.runtime_kernel.runtime_environment import EnvironmentEngine`
- `from sam.runtime_kernel.runtime_profile import ProfileEngine`
- `from sam.runtime_kernel.runtime_configuration import ConfigurationEngine`
- `from sam.runtime_kernel.conversation_runtime_context import (`
- `from sam.runtime_kernel.runtime_registry import (`
- `from sam.runtime_kernel.runtime_catalog import RuntimeCatalog`
- `from sam.runtime_kernel.runtime_locator import RuntimeLocator`
- `from sam.runtime_kernel.runtime_descriptor import DescriptorEngine`
- `from sam.runtime_kernel.runtime_manifest import ManifestEngine`
- `from sam.runtime_kernel.conversation_registry import ConversationRegistry, DashboardRegistry`
- `from sam.runtime_kernel.runtime_state import (`
- `from sam.runtime_kernel.state_machine import StateMachineEngine`
- `from sam.runtime_kernel.state_snapshot import SnapshotEngine`
- `from sam.runtime_kernel.state_history import StateHistory`
- `from sam.runtime_kernel.state_validator import StateValidator`
- `from sam.runtime_kernel.conversation_state import ConversationState, DashboardState`
- `from sam.runtime_kernel.runtime_lifecycle import (`
- `from sam.runtime_kernel.lifecycle_manager import LifecycleManager`
- *... and 48 more*

## `sam.sdk`

*No public exports defined.*

## `sam.service`

**Exported (4):**
- `ServiceManager`
- `generate_unit_file`
- `SYSTEMD_UNIT`
- `SAMService`

## `sam.storage`

*No public exports defined.*

## `sam.strategy`

**Exported (12):**
- `StrategicGoal`
- `StrategicGoalManager`
- `GOAL_HORIZONS`
- `GOAL_STATUSES`
- `LongTermObjective`
- `ObjectiveManager`
- `OBJECTIVE_STATUSES`
- `StrategicPlan`
- `StrategicPlanManager`
- `PLAN_STATUSES`
- `StrategyPlanner`
- `PHASE_TEMPLATES`

## `sam.telemetry`

**Exported (12):**
- `TelemetryEvent`
- `EventSeverity`
- `EventCategory`
- `TelemetryEventType`
- `Component`
- `TelemetryService`
- `RingBuffer`
- `Filter`
- `TelemetryStorage`
- `load_event_schema`
- `validate_against_schema`
- `event_stream`

## `sam.tuning`

**Exported (4):**
- `Autotuner`
- `MetricsCollector`
- `PerformanceMetric`
- `TuningSuggestion`

## `sam.web`

**Exported (2):**
- `app`
- `run_server`

## `sam.workflow`

**Exported (9):**
- `WorkflowDefinition`
- `WorkflowStep`
- `WorkflowTransition`
- `WorkflowParser`
- `WorkflowValidator`
- `WorkflowEngine`
- `WorkflowCheckpoint`
- `CheckpointStore`
- `CheckpointStatus`
