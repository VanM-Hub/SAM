"""
OP-376 — Recovery Startup

Fallback otomatis jika host utama gagal:

  Desktop → Console → Safe Mode → Headless

Semua downgrade dicatat. Tidak boleh crash — selalu akhiri dengan status.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from sam.launcher.host_manager import HostType
from sam.launcher.host_launcher import HostLauncher, HostLaunchResult
from sam.launcher.safe_mode import SafeModeManager, SafeMode
from sam.launcher.startup_report import StartupIssue, IssueSeverity


class FallbackLevel(Enum):
    """Level of fallback applied."""

    NONE = "none"
    SAFE_MODE = "safe_mode"
    HOST_DOWNGRADE = "host_downgrade"
    FULL_RECOVERY = "full_recovery"
    MINIMAL = "minimal"


@dataclass(frozen=True)
class RecoveryStep:
    """A single recovery step taken."""

    level: FallbackLevel
    action: str
    success: bool
    duration_ms: float = 0.0
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "action": self.action,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class RecoveryResult:
    """Result of the recovery process."""

    final_host: str
    final_safe_mode: str
    success: bool
    steps: List[RecoveryStep] = field(default_factory=list)
    issues: List[StartupIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_host": self.final_host,
            "final_safe_mode": self.final_safe_mode,
            "success": self.success,
            "steps": [s.to_dict() for s in self.steps],
        }


class RecoveryStartup:
    """Fallback startup chain.

    Chain:
      Target Host
      ↓ if fail
      Console (safe mode)
      ↓ if fail
      Safe Mode (minimal)
      ↓ if fail
      Headless (last resort)
    """

    FALLBACK_CHAIN: List[Tuple[HostType, str]] = [
        (HostType.DESKTOP, "target"),
        (HostType.CONSOLE, "fallback to console"),
        (HostType.HEADLESS, "fallback to headless"),
    ]

    def __init__(self, workspace: str = "") -> None:
        self._workspace = workspace or "."
        self._launcher = HostLauncher(workspace)

    def start(self, target_host: HostType) -> RecoveryResult:
        """Start the target host with automatic fallback on failure."""
        steps: List[RecoveryStep] = []
        issues: List[StartupIssue] = []
        current_safe_mode = SafeMode.NORMAL.value
        final_host = ""
        success = False

        # Determine initial chain based on target
        if target_host == HostType.DESKTOP:
            chain = self.FALLBACK_CHAIN
        elif target_host == HostType.CONSOLE:
            chain = self.FALLBACK_CHAIN[1:]  # skip desktop
        elif target_host == HostType.HEADLESS:
            chain = self.FALLBACK_CHAIN[2:]  # skip desktop, console
        else:
            chain = [(target_host, "target")]

        for host_type, action in chain:
            # Activate safe mode if needed
            if host_type in (HostType.CONSOLE, HostType.HEADLESS):
                safe_mgr = SafeModeManager(SafeMode.SAFE.value)
                current_safe_mode = SafeMode.SAFE.value

                step = RecoveryStep(
                    level=FallbackLevel.SAFE_MODE,
                    action=f"safe mode activated ({current_safe_mode})",
                    success=True,
                    detail="Safe mode: diagnostics+plugin discovery skipped",
                )
                steps.append(step)
            elif host_type == HostType.HEADLESS:
                safe_mgr = SafeModeManager(SafeMode.MINIMAL.value)
                current_safe_mode = SafeMode.MINIMAL.value

                step = RecoveryStep(
                    level=FallbackLevel.SAFE_MODE,
                    action=f"minimal safe mode ({current_safe_mode})",
                    success=True,
                    detail="Minimal mode: all optional checks skipped",
                )
                steps.append(step)

            # Attempt launch
            start = time.perf_counter()
            result = self._launcher.launch(host_type)
            dur = (time.perf_counter() - start) * 1000

            step = RecoveryStep(
                level=FallbackLevel.HOST_DOWNGRADE if action != "target" else FallbackLevel.NONE,
                action=f"{action}: {host_type.value}",
                success=result.success,
                duration_ms=round(dur, 1),
                detail=result.error or f"pid={result.pid}",
            )
            steps.append(step)

            if result.success:
                final_host = host_type.value
                success = True
                break

            issues.append(StartupIssue(
                stage="recovery",
                severity=IssueSeverity.WARNING,
                message=f"Host {host_type.value} failed: {result.error} — trying next",
            ))

        if not success:
            # Last resort: minimal diagnostics
            final_host = "diagnostics"
            current_safe_mode = SafeMode.MINIMAL.value
            mgr = SafeModeManager(SafeMode.MINIMAL.value)
            issues.append(StartupIssue(
                stage="recovery",
                severity=IssueSeverity.ERROR,
                message="All hosts failed. Entering diagnostics-only mode.",
            ))

        return RecoveryResult(
            final_host=final_host,
            final_safe_mode=current_safe_mode,
            success=success,
            steps=steps,
            issues=issues,
        )
