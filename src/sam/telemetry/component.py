from enum import Enum


class Component(str, Enum):
    """Komponen resmi SAM. Tidak boleh ada component baru tanpa registrasi."""
    RUNTIME = "runtime"
    GUARDIAN = "guardian"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    WORKFLOW = "workflow"
    PLANNER = "planner"
    EXECUTION = "execution"
    SAFETY = "safety"
    MISSION = "mission"
    POLICY = "policy"
    PLUGIN = "plugin"
    STORAGE = "storage"
    CLUSTER = "cluster"
    HOSTING = "hosting"
    TELEMETRY = "telemetry"
    OPERATIONS = "operations"
    DESKTOP = "desktop"
    API = "api"
    LANGUAGE = "language"

    @classmethod
    def list_all(cls) -> list:
        return [c.value for c in cls]
