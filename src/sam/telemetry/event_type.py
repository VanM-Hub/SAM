from enum import Enum


class TelemetryEventType(str, Enum):
    """Event resmi SAM. Gunakan Enum ini, bukan string."""

    # Runtime Lifecycle
    RUNTIME_STARTED = "runtime.started"
    RUNTIME_STOPPED = "runtime.stopped"
    RUNTIME_CRASHED = "runtime.crashed"
    RUNTIME_RECOVERING = "runtime.recovering"
    RUNTIME_READY = "runtime.ready"

    # Task / Workflow
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    # Knowledge
    KNOWLEDGE_LOADED = "knowledge.loaded"
    KNOWLEDGE_UPDATED = "knowledge.updated"
    KNOWLEDGE_SEARCHED = "knowledge.searched"
    KNOWLEDGE_FOUND = "knowledge.found"
    KNOWLEDGE_NOT_FOUND = "knowledge.not_found"

    # Memory
    MEMORY_RETRIEVED = "memory.retrieved"
    MEMORY_STORED = "memory.stored"
    MEMORY_CLEARED = "memory.cleared"

    # Plugin
    PLUGIN_INSTALLED = "plugin.installed"
    PLUGIN_ENABLED = "plugin.enabled"
    PLUGIN_DISABLED = "plugin.disabled"
    PLUGIN_UNINSTALLED = "plugin.uninstalled"
    PLUGIN_FAILED = "plugin.failed"

    # Mission & Guardian
    MISSION_CHANGED = "mission.changed"
    MISSION_HEALTH = "mission.health"
    GUARDIAN_ALERT = "guardian.alert"
    GUARDIAN_ACTION = "guardian.action"
    RECOMMENDATION_CREATED = "recommendation.created"

    # Component Health
    COMPONENT_HEALTHY = "component.healthy"
    COMPONENT_DEGRADED = "component.degraded"
    COMPONENT_FAILED = "component.failed"
    COMPONENT_RECOVERED = "component.recovered"

    # Operations / User
    OPERATOR_ACTION = "operator.action"
    OPERATOR_APPROVAL = "operator.approval"
    OPERATOR_DENIAL = "operator.denial"

    # System
    SYSTEM_BOOT = "system.boot"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"

    @classmethod
    def list_all(cls) -> list:
        return [e.value for e in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.list_all()
