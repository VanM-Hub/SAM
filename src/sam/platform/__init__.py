# Platform Experience - MISSION-3.5 (IP-3.5-001 Platform Workspace
#                + IP-3.5-002 Mission Experience
#                + IP-3.5-003 Citizen Experience
#                + IP-3.5-004 Explainability Experience
#                + IP-3.5-005 Platform Integration)
# AO-ENG-001 / Work Order MISSION-3.5 (2026-08-09, Engineering Started)
#
# Bounded context baru: src/sam/platform/ (KEPUTUSAN Option B, 2026-08-09).
# MISSION-3.5 TIDAK menambah governance/runtime/citizen/federation/authority.
# Ia MENYATUKAN seluruh capability yang sudah ada (SAM 2.x -> 3.4) menjadi
# satu pengalaman platform yang konsisten.
#
# Consumer-only: platform/ MENGONSUMSI capability yang ada via API publik /
# subpackage; TIDAK memodifikasi governance/runtime/citizen/federation,
# TIDAK mengubah authority.
# presentation/ tetap delivery/UI layer dan MENGONSUMSI platform/ (bukan
# tempat implementasi domain Platform Experience).
#
# Prinsip (roadmap SAM 3.5 - Platform Experience):
#   Powerful platform becomes usable platform.
#   Platform Experience presents governance. It never performs governance.
#   Presentation over implementation; Observation over intervention;
#   Visualization over orchestration; Explanation over abstraction;
#   Trust through transparency.
#
# Batas arsitektural platform/ (presentation-passive):
#   platform/ SHALL NOT: perform governance, perform approval, perform
#   execution, coordinate runtime, modify citizens, bypass runtime service,
#   create new authority, AI-controlled operation, distributed execution.
#   platform/ MENGONSUMSI & MENYAJIKAN; never performs.
#
# IP-3.5-001 (Platform Workspace) - Guardrail PEX-01..10 (compliance.py):
#   Workspace != Governance; Navigation != Execution; Perspective != Authority;
#   Context != State Control; Layout != Orchestration;
#   Descriptor != Contract Execution; View != Intervention;
#   Presentation Passive; Consumer-only; Read-only API.
#
# Version: dimulai 3.5.0 (IP-3.5-001).

# IP-3.5-001 - Platform Workspace (WP-01..08)
from sam.platform.workspace_model import (
    PlatformDomain,
    Perspective,
    PerspectiveBinding,
    WorkspaceModel,
    build_domain,
    build_perspective,
)
from sam.platform.navigation import NavigationModel, NavigationRoute, build_navigation
from sam.platform.perspective import PerspectiveRegistry, PerspectiveState
from sam.platform.context import WorkspaceContext, ContextStore
from sam.platform.layout import LayoutModel, PanelSlot
from sam.platform.descriptor import WorkspaceDescriptor, descriptor_from_model
from sam.platform.workspace_api import WorkspaceAPI, WorkspaceSnapshot, default_workspace
from sam.platform.compliance import ComplianceResult, compliance_check

# IP-3.5-002 - Mission Experience (WP-09..16)
from sam.platform.mission_workspace import (
    MissionInput,
    MissionTimelineInput,
    MissionHealthInput,
    MissionJourney,
    MissionJourneyStep,
    MissionWorkspaceView,
    build_journey,
)
from sam.platform.mission_timeline import (
    MissionTimelineView,
    MissionProgress,
    compute_progress,
    timeline_from_checkpoints,
)
from sam.platform.mission_context import (
    MissionContext,
    MissionInsight,
    build_insight,
)
from sam.platform.mission_api import MissionAPI, MissionSnapshot
from sam.platform.compliance import mission_compliance_check

__version__ = "3.5.0"

__all__ = [
    # WP-01 model
    "PlatformDomain",
    "Perspective",
    "PerspectiveBinding",
    "WorkspaceModel",
    "build_domain",
    "build_perspective",
    # WP-02 navigation
    "NavigationModel",
    "NavigationRoute",
    "build_navigation",
    # WP-03 perspective
    "PerspectiveRegistry",
    "PerspectiveState",
    # WP-04 context
    "WorkspaceContext",
    "ContextStore",
    # WP-05 layout
    "LayoutModel",
    "PanelSlot",
    # WP-06 descriptor
    "WorkspaceDescriptor",
    "descriptor_from_model",
    # WP-07 api
    "WorkspaceAPI",
    "WorkspaceSnapshot",
    "default_workspace",
    # WP-08 compliance
    "ComplianceResult",
    "compliance_check",
    # WP-09 mission workspace
    "MissionInput",
    "MissionTimelineInput",
    "MissionHealthInput",
    "MissionJourney",
    "MissionJourneyStep",
    "MissionWorkspaceView",
    "build_journey",
    # WP-10/12 timeline & progress
    "MissionTimelineView",
    "MissionProgress",
    "compute_progress",
    "timeline_from_checkpoints",
    # WP-13/14 context & insight
    "MissionContext",
    "MissionInsight",
    "build_insight",
    # WP-15 mission api
    "MissionAPI",
    "MissionSnapshot",
    # WP-16 mission compliance
    "mission_compliance_check",
]
