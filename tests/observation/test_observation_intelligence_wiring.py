"""Tests for C-Phase 3 (Workstream C1-C5): Observation wiring shortcuts.

Memverifikasi wiring get_*_observer + observe_* menghasilkan laporan intel
melalui jalur publikasi read-only, dan registry tidak berubah.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.api.observation_wiring import (
    get_publication_registry,
    get_mission_intelligence_observer,
    get_workflow_intelligence_observer,
    get_approval_intelligence_observer,
    get_execution_intelligence_observer,
    get_audit_intelligence_observer,
    observe_mission,
    observe_workflows,
    observe_approvals,
    observe_executions,
    observe_audits,
)


class TestWiringObservers:
    def test_all_observers_are_singletons(self):
        assert get_mission_intelligence_observer() is get_mission_intelligence_observer()
        assert get_workflow_intelligence_observer() is get_workflow_intelligence_observer()
        assert get_approval_intelligence_observer() is get_approval_intelligence_observer()
        assert get_execution_intelligence_observer() is get_execution_intelligence_observer()
        assert get_audit_intelligence_observer() is get_audit_intelligence_observer()


class TestWiringShortcuts:
    def test_mission_shortcut(self):
        rep = observe_mission()
        assert rep.mission_id == "mission"
        assert rep.timeline is not None

    def test_workflow_shortcut(self):
        rep = observe_workflows()
        assert rep.total_workflows >= 0

    def test_approval_shortcut(self):
        rep = observe_approvals()
        assert rep.queue is not None

    def test_execution_shortcut(self):
        rep = observe_executions()
        assert rep.timeline is not None

    def test_audit_shortcut(self):
        rep = observe_audits()
        assert rep.correlation is not None


class TestWiringReadOnly:
    def test_registry_unchanged_after_all_shortcuts(self):
        reg = get_publication_registry()
        before = reg.observe_all().runtime_count
        observe_mission()
        observe_workflows()
        observe_approvals()
        observe_executions()
        observe_audits()
        after = reg.observe_all().runtime_count
        assert before == after == 10
