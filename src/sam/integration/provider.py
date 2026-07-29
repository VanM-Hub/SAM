# OP-403 — External Provider Runtime (Mock)
from typing import Tuple, List
from .contracts import IntegrationProtocol, IntegrationDescriptor, IntegrationCapability, IntegrationRequest, IntegrationResponse, IntegrationPreview, IntegrationHealth

class BaseIntegration:
    def __init__(self, itype, name, version="1.0.0", description=""):
        self._id = name.lower().replace(" ","_")
        self._itype = itype; self._name = name; self._version = version; self._description = description
        self._capabilities = []; self._healthy = True
    @property
    def descriptor(self):
        return IntegrationDescriptor(integration_id=self._id, integration_type=self._itype, name=self._name, version=self._version, healthy=self._healthy, capability_names=tuple(c.name for c in self._capabilities))
    def preview(self, req):
        return IntegrationResponse(success=True, preview=IntegrationPreview(success=True, summary=f"[{self._name}] {req.action} -> {req.target}", integration_type=self._itype, can_rollback=True))
    def supported_actions(self):
        acts = []; [acts.extend(c.actions) for c in self._capabilities]; return tuple(dict.fromkeys(acts))
    def health(self): return IntegrationHealth(healthy=self._healthy, integration_type=self._itype, name=self._name, version=self._version)
    def add_capability(self, cap): self._capabilities.append(cap)
    def set_health(self, h): self._healthy = h

class MockSlackIntegration(BaseIntegration):
    def __init__(self):
        super().__init__("slack","Mock Slack"); self.add_capability(IntegrationCapability("notify","Send Slack message",("notify","read"),"slack",False,"low"))
    def preview(self, req):
        m=req.payload.get("message",""); t=req.target or "general"
        return IntegrationResponse(success=True, preview=IntegrationPreview(success=True, summary=f"[SLACK] {req.action} -> #{t}: {m}", integration_type="slack"))

class MockDiscordIntegration(BaseIntegration):
    def __init__(self):
        super().__init__("discord","Mock Discord"); self.add_capability(IntegrationCapability("notify","Send Discord message",("notify","read"),"discord",False,"low"))
    def preview(self, req):
        m=req.payload.get("message",""); t=req.target or "general"
        return IntegrationResponse(success=True, preview=IntegrationPreview(success=True, summary=f"[DISCORD] {req.action} -> #{t}: {m}", integration_type="discord"))

class MockEmailIntegration(BaseIntegration):
    def __init__(self):
        super().__init__("email","Mock Email"); self.add_capability(IntegrationCapability("notify","Send email",("notify",),"email",True,"low"))
    def preview(self, req):
        to=req.payload.get("to","user@example.com"); s=req.payload.get("subject","")
        return IntegrationResponse(success=True, preview=IntegrationPreview(success=True, summary=f"[EMAIL] {req.action} -> {to}: {s}", integration_type="email"))

class MockWebhookIntegration(BaseIntegration):
    def __init__(self):
        super().__init__("webhook","Mock Webhook"); self.add_capability(IntegrationCapability("notify","Send webhook",("notify","create"),"webhook",True,"medium"))
    def preview(self, req):
        url=req.payload.get("url",req.target or "https://hook.example.com")
        return IntegrationResponse(success=True, preview=IntegrationPreview(success=True, summary=f"[WEBHOOK] {req.action} -> {url}", integration_type="webhook"))

class MockRESTIntegration(BaseIntegration):
    def __init__(self):
        super().__init__("rest","Mock REST API"); self.add_capability(IntegrationCapability("read","HTTP GET",("read","search"),"rest",False,"low"))
        self.add_capability(IntegrationCapability("write","HTTP PUT/POST",("write","create"),"rest",True,"medium"))
        self.add_capability(IntegrationCapability("delete","HTTP DELETE",("delete",),"rest",True,"high"))
    def preview(self, req):
        endpoint=req.payload.get("endpoint",req.target or "/api")
        m={"read":"GET","write":"PUT","create":"POST","delete":"DELETE","search":"GET"}.get(req.action,"GET")
        return IntegrationResponse(success=True, preview=IntegrationPreview(success=True, summary=f"[REST] {m} {endpoint}", integration_type="rest"))

class MockFilesystemIntegration(BaseIntegration):
    def __init__(self):
        super().__init__("filesystem","Mock Filesystem"); self.add_capability(IntegrationCapability("read","Read file",("read","search"),"filesystem",False,"low"))
        self.add_capability(IntegrationCapability("write","Write file",("write","create"),"filesystem",True,"medium"))
        self.add_capability(IntegrationCapability("delete","Delete file",("delete",),"filesystem",True,"high"))
    def preview(self, req):
        path=req.payload.get("path",req.target or "/tmp")
        return IntegrationResponse(success=True, preview=IntegrationPreview(success=True, summary=f"[FS] {req.action} -> {path}", integration_type="filesystem"))
