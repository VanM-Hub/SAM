# OP-405 — Mock Connectors
# Python 3.8, frozen DTO, synchronous, no execute/network/subprocess
# All connectors are preview-only — no real execution

from sam.execution.connector_protocol import BaseConnector, ConnectorCapability
from sam.execution.execution_request import ExecutionRequest, ExecutionTarget, ExecutionParameter

from typing import Tuple

from .connector_capability import CapabilitySet, Capability


class MockFilesystemConnector(BaseConnector):
    """Mock filesystem connector — preview only, no real file I/O."""

    def __init__(self, name: str = "Mock Filesystem",
                 version: str = "1.0.0") -> None:
        super().__init__(name, "filesystem", version,
                         "Mock connector for filesystem operations (preview only)")
        caps = CapabilitySet(tuple(Capability.builtin(n) for n in
                                    ["read", "write", "create", "delete", "search"]))
        for cap in caps.capabilities:
            self.add_capability(ConnectorCapability(
                action=cap.name,
                description=cap.description,
                requires_approval=cap.requires_approval,
                risk_level=cap.risk_level,
            ))

    def preview(self, request: ExecutionRequest) -> str:
        target = request.target
        tname = target.name if target else "unknown"
        params = {p.key: p.value for p in request.parameters}
        path = params.get("path", tname)

        if request.action == "read":
            return f"[PREVIEW] Read file: {path}"
        elif request.action == "write":
            return f"[PREVIEW] Write to file: {path}"
        elif request.action == "create":
            return f"[PREVIEW] Create file: {path}"
        elif request.action == "delete":
            return f"[PREVIEW] Delete file: {path} (risk: high)"
        elif request.action == "search":
            query = params.get("query", "*")
            return f"[PREVIEW] Search files: {path} with pattern '{query}'"
        return f"[PREVIEW] {request.action} on {tname}"


class MockRESTConnector(BaseConnector):
    """Mock REST API connector — preview only, no real HTTP calls."""

    def __init__(self, name: str = "Mock REST API",
                 version: str = "1.0.0") -> None:
        super().__init__(name, "rest_api", version,
                         "Mock connector for REST API operations (preview only)")
        caps = CapabilitySet(tuple(Capability.builtin(n) for n in
                                    ["read", "write", "create", "delete",
                                     "search", "monitor", "notify"]))
        for cap in caps.capabilities:
            self.add_capability(ConnectorCapability(
                action=cap.name,
                description=cap.description,
                requires_approval=cap.requires_approval,
                risk_level=cap.risk_level,
            ))

    def preview(self, request: ExecutionRequest) -> str:
        target = request.target
        tname = target.name if target else "unknown"
        params = {p.key: p.value for p in request.parameters}
        endpoint = params.get("endpoint", tname)

        if request.action == "read":
            return f"[PREVIEW] GET {endpoint}"
        elif request.action == "write":
            return f"[PREVIEW] PUT {endpoint}"
        elif request.action == "create":
            return f"[PREVIEW] POST {endpoint}"
        elif request.action == "delete":
            return f"[PREVIEW] DELETE {endpoint} (risk: high)"
        elif request.action == "search":
            return f"[PREVIEW] GET {endpoint}?search={params.get('query', '')}"
        elif request.action == "monitor":
            return f"[PREVIEW] Monitor {endpoint}"
        elif request.action == "notify":
            return f"[PREVIEW] Notify {endpoint}: {params.get('message', '')}"
        return f"[PREVIEW] REST {request.action.upper()} on {tname}"


class MockGitConnector(BaseConnector):
    """Mock Git connector — preview only, no real Git operations."""

    def __init__(self, name: str = "Mock Git",
                 version: str = "1.0.0") -> None:
        super().__init__(name, "git", version,
                         "Mock connector for Git operations (preview only)")
        caps = CapabilitySet(tuple(Capability.builtin(n) for n in
                                    ["read", "write", "create", "delete",
                                     "search", "rollback"]))
        for cap in caps.capabilities:
            self.add_capability(ConnectorCapability(
                action=cap.name,
                description=cap.description,
                requires_approval=cap.requires_approval,
                risk_level=cap.risk_level,
            ))

    def preview(self, request: ExecutionRequest) -> str:
        target = request.target
        tname = target.name if target else "unknown"
        params = {p.key: p.value for p in request.parameters}
        repo = params.get("repo", tname)

        if request.action == "read":
            return f"[PREVIEW] Git read/clone: {repo}"
        elif request.action == "write":
            branch = params.get("branch", "main")
            return f"[PREVIEW] Git push to {repo}/{branch}"
        elif request.action == "create":
            return f"[PREVIEW] Git init/checkout: {repo}"
        elif request.action == "delete":
            branch = params.get("branch", "")
            return f"[PREVIEW] Git delete branch/commit: {repo}/{branch} (risk: high)"
        elif request.action == "search":
            return f"[PREVIEW] Git log search: {repo}"
        elif request.action == "rollback":
            commit = params.get("commit", "HEAD~1")
            return f"[PREVIEW] Git revert to {commit} on {repo} (risk: high)"
        return f"[PREVIEW] Git {request.action} on {tname}"


class MockShellConnector(BaseConnector):
    """Mock Shell command connector — preview only, no real execution."""

    def __init__(self, name: str = "Mock Shell",
                 version: str = "1.0.0") -> None:
        super().__init__(name, "shell", version,
                         "Mock connector for shell commands (preview only)")
        # Minimal capabilities — shell is high risk
        for cap_name in ["read", "monitor", "execute", "search"]:
            cap = Capability.builtin(cap_name)
            self.add_capability(ConnectorCapability(
                action=cap.name,
                description=cap.description,
                requires_approval=True,
                risk_level="high",
            ))

    def preview(self, request: ExecutionRequest) -> str:
        target = request.target
        tname = target.name if target else "unknown"
        params = {p.key: p.value for p in request.parameters}
        command = params.get("command", tname)

        if request.action == "read":
            return f"[PREVIEW] Shell cat/less: {command}"
        elif request.action == "monitor":
            return f"[PREVIEW] Shell tail/watch: {command}"
        elif request.action == "execute":
            return f"[PREVIEW] Shell execute: {command} (risk: high, needs approval)"
        elif request.action == "search":
            pattern = params.get("pattern", "")
            return f"[PREVIEW] Shell grep: {command} for '{pattern}'"
        return f"[PREVIEW] Shell {request.action}: {command}"

    def validate(self, request: ExecutionRequest) -> Tuple[str, ...]:
        errors = list(super().validate(request))
        if request.action == "execute":
            target = request.target
            tname = target.name if target else ""
            if not tname:
                errors.append("Shell execute requires a target command")
        return tuple(errors)
