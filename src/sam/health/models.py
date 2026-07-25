"""Health models for SAM Framework.

Provides standardized health check status and reporting structures.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck(BaseModel):
    """Individual health check result for a component."""

    component: str
    status: HealthStatus
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class ComponentHealth(BaseModel):
    """Health status of a single component with nested checks."""

    component: str
    status: HealthStatus
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    checks: List[HealthCheck] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    def add_check(self, check: HealthCheck) -> None:
        """Add a nested health check."""
        self.checks.append(check)
        # Update overall status based on worst check
        self._update_status_from_checks()

    def _update_status_from_checks(self) -> None:
        """Derive overall status from nested checks."""
        if not self.checks:
            return
        statuses = [c.status for c in self.checks]
        if HealthStatus.UNHEALTHY in statuses:
            self.status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            self.status = HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            self.status = HealthStatus.UNKNOWN
        else:
            self.status = HealthStatus.HEALTHY

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checks": [c.to_dict() for c in self.checks],
            "timestamp": self.timestamp.isoformat(),
        }


class HealthReport(BaseModel):
    """Aggregated health report for all components."""

    status: HealthStatus = HealthStatus.UNKNOWN
    components: List[ComponentHealth] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    def add_component(self, component: ComponentHealth) -> None:
        """Add a component health to the report."""
        self.components.append(component)
        self._update_overall_status()

    def _update_overall_status(self) -> None:
        """Derive overall status from component statuses."""
        if not self.components:
            self.status = HealthStatus.UNKNOWN
            return
        statuses = [c.status for c in self.components]
        if HealthStatus.UNHEALTHY in statuses:
            self.status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            self.status = HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            self.status = HealthStatus.UNKNOWN
        else:
            self.status = HealthStatus.HEALTHY

    def to_markdown(self) -> str:
        """Format report as Markdown table."""
        lines = [
            f"# Health Report",
            f"",
            f"**Overall Status**: `{self.status.value.upper()}`",
            f"**Timestamp**: {self.timestamp.isoformat()}",
            f"",
            f"## Components",
            f"",
            f"| Component | Status | Message |",
            f"|-----------|--------|---------|",
        ]
        for comp in self.components:
            status_emoji = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNHEALTHY: "❌",
                HealthStatus.UNKNOWN: "❓",
            }.get(comp.status, "❓")
            msg = comp.message or ""
            lines.append(f"| {comp.component} | {status_emoji} {comp.status.value} | {msg} |")
            if comp.checks:
                lines.append(f"")
                lines.append(f"### {comp.component} Checks")
                lines.append(f"")
                lines.append(f"| Check | Status | Message |")
                lines.append(f"|-------|--------|---------|")
                for check in comp.checks:
                    lines.append(f"| {check.component} | {check.status.value} | {check.message or ''} |")
        lines.append(f"")
        if self.metadata:
            lines.append(f"## Metadata")
            lines.append(f"")
            for k, v in self.metadata.items():
                lines.append(f"- **{k}**: {v}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "components": [c.to_dict() for c in self.components],
            "metadata": self.metadata,
        }