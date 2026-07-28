"""
SecurityObserver — Observation layer untuk security.

Observation (belum enforcement):
  - permission
  - credential
  - certificate
  - secret
  - policy
  - plugin signature

Belum ada enforcement. Hanya observasi.
"""

import structlog
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import stat


logger = structlog.get_logger()


@dataclass
class SecurityObservation:
    """Satu observasi keamanan."""
    category: str           # permission, credential, certificate, secret, policy, signature
    severity: str           # information, warning, critical
    detail: str
    evidence: List[str] = field(default_factory=list)
    recommendation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_text(self) -> str:
        return "[{severity}] {category}: {detail}".format(
            severity=self.severity.upper(),
            category=self.category,
            detail=self.detail,
        )


class SecurityObserver:
    """Observasi keamanan dari sumber yang tersedia."""

    def __init__(self, workspace_provider=None, runtime_provider=None):
        self._wp = workspace_provider
        self._rp = runtime_provider

    def observe_all(self) -> List[SecurityObservation]:
        """Observasi semua aspek keamanan."""
        observations = []

        # Permission — cek writability direktori
        observations.extend(self._observe_permissions())

        # Secret — cek env variables
        observations.extend(self._observe_secrets())

        # Policy — cek default
        observations.extend(self._observe_policies())

        # Signature — cek plugin signature
        observations.extend(self._observe_signatures())

        if observations:
            logger.info("security_observation_completed",
                count=len(observations),
                severities=[o.severity for o in observations],
            )

        return observations

    def get_summary(self) -> str:
        """Ringkasan security observation."""
        obs = self.observe_all()
        if not obs:
            return "No security concerns detected."
        critical = [o for o in obs if o.severity == "critical"]
        warnings = [o for o in obs if o.severity == "warning"]
        info = [o for o in obs if o.severity == "information"]

        parts = []
        if critical:
            parts.append("{} critical".format(len(critical)))
        if warnings:
            parts.append("{} warning".format(len(warnings)))
        if info:
            parts.append("{} info".format(len(info)))
        return "Security: {} issue(s) — {}".format(len(obs), ", ".join(parts))

    def _observe_permissions(self) -> List[SecurityObservation]:
        """Cek permission — workspace writability, world-readable files (summary)."""
        observations = []

        if self._wp:
            try:
                ws = self._wp.observe()
                if not ws.workspace.writable:
                    observations.append(SecurityObservation(
                        category="permission",
                        severity="warning",
                        detail="Workspace is not writable",
                        evidence=["Path: {}".format(ws.workspace.path)],
                        recommendation="Check workspace permissions",
                    ))

                # Cek file permission — cukup satu observasi summary
                target_path = getattr(ws.workspace, 'path', '.')
                world_readable_count = 0
                if os.path.isdir(target_path):
                    for root, dirs, files in os.walk(target_path):
                        for fname in files:
                            if len(files) > 100:  # limit scan depth
                                break
                            fpath = os.path.join(root, fname)
                            try:
                                mode = os.stat(fpath).st_mode
                                if mode & stat.S_IROTH:
                                    world_readable_count += 1
                            except OSError:
                                pass

                if world_readable_count > 0:
                    observations.append(SecurityObservation(
                        category="permission",
                        severity="information",
                        detail="{} world-readable file(s) in workspace".format(world_readable_count),
                        evidence=["Scan: {}".format(target_path)],
                        recommendation="Restrict file permissions for sensitive files",
                    ))
            except Exception:
                pass

        return observations

    def _observe_secrets(self) -> List[SecurityObservation]:
        """Cek secret di environment variable."""
        observations = []
        sensitive_vars = ["TOKEN", "SECRET", "PASSWORD", "KEY", "CREDENTIAL", "AUTH"]

        for var in sensitive_vars:
            for key, val in os.environ.items():
                if var.lower() in key.lower() and val and val != "<not set>":
                    observations.append(SecurityObservation(
                        category="credential",
                        severity="information",
                        detail="Environment variable '{}' contains potential credential".format(key),
                        evidence=["{}={}".format(key, val[:4] + "****")],
                        recommendation="Rotate if compromised",
                    ))
                    break  # cukup satu per tipe

        return observations

    def _observe_policies(self) -> List[SecurityObservation]:
        """Cek policy — apakah ada policy yang terlalu permisif."""
        observations = []

        # Cek PYTHONPATH — potensi code injection
        pp = os.environ.get("PYTHONPATH", "")
        if pp and ("." in pp or "src" in pp):
            observations.append(SecurityObservation(
                category="policy",
                severity="information",
                detail="PYTHONPATH includes local directory — potential code injection risk",
                evidence=["PYTHONPATH={}".format(pp)],
                recommendation="Pin PYTHONPATH to absolute paths only",
            ))

        return observations

    def _observe_signatures(self) -> List[SecurityObservation]:
        """Cek plugin signature — apakah ada plugin unsigned."""
        observations = []

        try:
            # Cek directory plugin
            plugin_dirs = [
                os.path.join(os.getcwd(), "plugins"),
                os.path.join(os.getcwd(), "src", "sam", "plugin"),
            ]
            for pdir in plugin_dirs:
                if os.path.isdir(pdir):
                    for item in os.listdir(pdir):
                        if item.endswith(".py") and item != "__init__.py":
                            observations.append(SecurityObservation(
                                category="signature",
                                severity="information",
                                detail="Unsigned plugin: {}".format(item),
                                evidence=["Path: {}/{}".format(pdir, item)],
                                recommendation="Verify plugin authenticity",
                            ))
        except Exception:
            pass

        return observations
