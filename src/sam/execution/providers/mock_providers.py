# OP-443 — Mock Providers
# Python 3.8, frozen DTO, synchronous, preview only

from .provider_protocol import BaseProvider, ProviderCapability, ProviderRequest, ProviderResponse
from sam.execution.adapters.execution_envelope import ExecutionEnvelope


class MockFilesystemProvider(BaseProvider):
    def __init__(self):
        super().__init__("filesystem", "Mock Filesystem Provider", "1.0.0", "Mock filesystem provider")
        self.add_capability(ProviderCapability("read","Read files",("read",),"filesystem",False,"low"))
        self.add_capability(ProviderCapability("write","Write files",("write",),"filesystem",True,"medium"))
        self.add_capability(ProviderCapability("create","Create files",("create",),"filesystem",True,"medium"))
        self.add_capability(ProviderCapability("delete","Delete files",("delete",),"filesystem",True,"high"))
        self.add_capability(ProviderCapability("search","Search files",("search",),"filesystem",False,"low"))

    def execute_preview(self, request: ProviderRequest) -> ProviderResponse:
        actions = [f"[FS] {i.action} -> {i.target}" for i in (request.envelope.items if request.envelope else [])]
        return ProviderResponse(success=True, preview="\n".join(actions),
            estimated_duration=len(request.envelope.items)*1 if request.envelope else 0,
            affected_resources=tuple(i.target for i in request.envelope.items) if request.envelope else (),
            provider_type="filesystem")


class MockProcessProvider(BaseProvider):
    def __init__(self):
        super().__init__("process", "Mock Process Provider", "1.0.0", "Mock process/command provider")
        self.add_capability(ProviderCapability("execute","Execute command",("execute",),"process",True,"high"))
        self.add_capability(ProviderCapability("monitor","Monitor process",("monitor","read"),"process",True,"medium"))

    def execute_preview(self, request: ProviderRequest) -> ProviderResponse:
        actions = [f"[PROC] {i.action} -> {i.target} (PREVIEW ONLY)" for i in (request.envelope.items if request.envelope else [])]
        return ProviderResponse(success=True, preview="\n".join(actions),
            estimated_duration=5, rollback_available=True, provider_type="process",
            affected_resources=("process","stdout","stderr"))


class MockHttpProvider(BaseProvider):
    def __init__(self):
        super().__init__("http", "Mock HTTP Provider", "1.0.0", "Mock HTTP/REST provider")
        self.add_capability(ProviderCapability("read","HTTP GET",("read",),"http",False,"low"))
        self.add_capability(ProviderCapability("write","HTTP POST/PUT",("write","create"),"http",True,"medium"))
        self.add_capability(ProviderCapability("delete","HTTP DELETE",("delete",),"http",True,"high"))
        self.add_capability(ProviderCapability("notify","HTTP notification",("notify",),"http",True,"low"))

    def execute_preview(self, request: ProviderRequest) -> ProviderResponse:
        actions = [f"[HTTP] {i.action} -> {i.target}" for i in (request.envelope.items if request.envelope else [])]
        return ProviderResponse(success=True, preview="\n".join(actions),
            estimated_duration=len(request.envelope.items)*2 if request.envelope else 0,
            affected_resources=tuple(f"endpoint:{i.target}" for i in request.envelope.items) if request.envelope else (),
            provider_type="http")


class MockDatabaseProvider(BaseProvider):
    def __init__(self):
        super().__init__("database", "Mock Database Provider", "1.0.0", "Mock database provider")
        self.add_capability(ProviderCapability("read","Query data",("read","search"),"database",False,"low"))
        self.add_capability(ProviderCapability("write","Write data",("write","create","delete"),"database",True,"high"))

    def execute_preview(self, request: ProviderRequest) -> ProviderResponse:
        actions = [f"[DB] {i.action} -> {i.target}" for i in (request.envelope.items if request.envelope else [])]
        return ProviderResponse(success=True, preview="\n".join(actions),
            estimated_duration=3, provider_type="database",
            affected_resources=tuple(i.target for i in request.envelope.items) if request.envelope else ())


class MockNotificationProvider(BaseProvider):
    def __init__(self):
        super().__init__("notification", "Mock Notification Provider", "1.0.0", "Mock notification provider")
        self.add_capability(ProviderCapability("notify","Send notification",("notify",),"notification",True,"low"))
        self.add_capability(ProviderCapability("monitor","Monitor events",("monitor","read"),"notification",False,"low"))

    def execute_preview(self, request: ProviderRequest) -> ProviderResponse:
        actions = [f"[NOTIFY] {i.action} -> {i.target}" for i in (request.envelope.items if request.envelope else [])]
        return ProviderResponse(success=True, preview="\n".join(actions),
            estimated_duration=1, provider_type="notification",
            affected_resources=tuple(i.target for i in request.envelope.items) if request.envelope else ())
