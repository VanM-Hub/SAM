"""Shared fixtures for governance_intelligence tests (IP-3.1-001)."""

import pytest

from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.indexes import index_mission
from sam.governance_intelligence.knowledge.repository import (
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.knowledge.query import KnowledgeQueryAPI

SAMPLE_MISSION = (
    "# Mission\n"
    "SAM exists to solve one fundamental problem.\n"
    "\n"
    "# Objective\n"
    "Govern the complete lifecycle of intelligence.\n"
    "\n"
    "# Scope\n"
    "Mission definition, workflow governance.\n"
    "\n"
    "# Lifecycle\n"
    "Assessment, Evidence, Validation, Baseline CI, Operational.\n"
)

SAMPLE_GOVERNANCE = (
    "# Policy Approval\n"
    "Approve only with evidence.\n"
    "\n"
    "# Workflow Runtime\n"
    "Workflow requires approval before execution.\n"
    "\n"
    "# Approval Gate\n"
    "Approval is mandatory.\n"
)


@pytest.fixture
def mission_content():
    return SAMPLE_MISSION


@pytest.fixture
def mission_repo():
    idx = index_mission("docs/foundation/MISSION.md", SAMPLE_MISSION)
    return MissionRepository(idx)


@pytest.fixture
def evidence_repo():
    idx = load_index("evidence", "docs/foundation/MISSION.md", "evidence", SAMPLE_MISSION)
    return EvidenceRepository(idx)


@pytest.fixture
def policy_repo():
    idx = index_governance("docs/governance.md", SAMPLE_GOVERNANCE)
    return PolicyRepository(idx)


@pytest.fixture
def runtime_repo():
    idx = index_governance("docs/governance.md", SAMPLE_GOVERNANCE)
    return RuntimeRepository(idx)


@pytest.fixture
def query_api():
    return KnowledgeQueryAPI()


from sam.governance_intelligence.knowledge.indexes import index_governance  # noqa: E402
