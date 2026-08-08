# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Mission Runtime — Contract suite (WP-B2).

Membuktikan kontrak lintas-lapisan Mission pada sub-domain Objective, Resource,
Timeline, State, dan Coordination, memakai API publik `sam.mission_runtime`.
Pure test — tidak mengubah source.

Signatures diverifikasi dari source:
- ObjectiveBuilder(registry).add() / ObjectiveValidator(registry).validate()
- ResourceInventory().add/ get; ResourceAllocator(inventory).allocate()
- TimelineBuilder().build(); MissionTimeline(mission_id, checkpoints).checkpoint_count
- StateRegistry().set/get; StateTransition(mission_id, from_state, to_state).changed
- CoordinationRegistry().register; MissionCoordinator(registry).coordinate
- MissionCertifier().certify -> CertificationResult(certified, criteria)
"""

from __future__ import annotations

import pytest

from sam.mission_runtime import (
    ObjectiveRegistry,
    ObjectiveBuilder,
    ObjectiveValidator,
    ObjectiveSummary,
    ResourceInventory,
    ResourceAllocator,
    ResourceSummary,
    ResourceDescriptor,
    TimelineBuilder,
    TimelineValidator,
    MissionTimeline,
    TimelineCheckpoint,
    TimelineSummary,
    StateRegistry,
    StateTransition,
    MissionState,
    StateValidator,
    StateHistory,
    CoordinationRegistry,
    CoordinationPlan,
    CoordinationValidator,
    CoordinationSummary,
    MissionCoordinator,
    MissionCertifier,
    CertificationCriterion,
    CertificationResult,
)


class TestObjectiveContract:
    def test_objective_registry_register_and_validate(self):
        reg = ObjectiveRegistry()
        builder = ObjectiveBuilder(reg)
        builder.add(objective_id="o1", title="Objektif 1")
        assert reg.count() >= 1
        validator = ObjectiveValidator(reg)
        report = validator.validate()
        assert report is not None

    def test_objective_summary_totals(self):
        s = ObjectiveSummary(mission_id="m", objective_ids=("o1", "o2"), total=2)
        assert s.total == 2


class TestResourceContract:
    def test_resource_inventory_add_and_query(self):
        inv = ResourceInventory()
        inv.add(ResourceDescriptor(resource_id="r1", name="CPU", capacity=100))
        assert inv.count() >= 1
        assert inv.get("r1") is not None

    def test_resource_allocator_allocate(self):
        inv = ResourceInventory()
        inv.add(ResourceDescriptor(resource_id="r1", capacity=10))
        allocator = ResourceAllocator(inv)
        result = allocator.allocate()
        # allocation mengembalikan ResourceAllocation dengan hitungan resource
        assert result is not None
        assert result.count >= 1
        assert len(result.ids) >= 1

    def test_resource_summary_and_descriptor(self):
        rs = ResourceSummary(allocated_ids=("r1",), total=1)
        assert rs.total == 1
        rd = ResourceDescriptor(resource_id="r1", name="CPU", available=True, capacity=8)
        assert rd.capacity == 8
        assert rd.available is True


class TestTimelineContract:
    def test_timeline_build_and_checkpoint_count(self):
        builder = TimelineBuilder()
        timeline = builder.build(mission_id="m-tl", labels=("mulai", "tengah", "selesai"))
        assert timeline.checkpoint_count == 3

    def test_checkpoint_constructible(self):
        cp = TimelineCheckpoint(checkpoint_id="c1", order=1, label="mulai")
        assert cp.order == 1 and cp.label == "mulai"


class TestStateContract:
    def test_state_registry_set_get(self):
        reg = StateRegistry()
        state = MissionState(mission_id="m-st", state="planning")
        reg.set(state)
        assert reg.count() >= 1
        got = reg.get("m-st")
        assert got is not None
        assert got.state == "planning"

    def test_state_transition_changed(self):
        t = StateTransition(mission_id="m-st", from_state="planning", to_state="executing")
        assert t.changed is True
        same = StateTransition(mission_id="m2", from_state="a", to_state="a")
        assert same.changed is False

    def test_state_history_record_events(self):
        h = StateHistory()
        before = h.count()
        t = StateTransition(mission_id="m-h", from_state="open", to_state="validated")
        h.record(t)
        assert h.count() >= before + 1
        assert len(h.events()) >= before + 1


class TestCoordinationContract:
    def test_coordination_registry_and_plan(self):
        reg = CoordinationRegistry()
        plan = CoordinationPlan(mission_id="m", runtimes=("policy", "workflow"))
        reg.register(plan)
        assert reg.count() >= 1
        assert plan.runtime_count >= 2
        assert plan.is_plan_only is not None

    def test_coordinator_coordinates(self):
        reg = CoordinationRegistry()
        plan = CoordinationPlan(mission_id="m", runtimes=("memory", "knowledge"))
        reg.register(plan)
        coord = MissionCoordinator(reg)
        result = coord.coordinate(mission_id="m", runtimes=("memory", "knowledge"))
        assert result is not None
        assert result.mission_id == "m"


class TestCertificationContract:
    def test_certification_result_met_count(self):
        c1 = CertificationCriterion(name="evidence", met=True)
        c2 = CertificationCriterion(name="baseline", met=False)
        res = CertificationResult(certified=False, criteria=(c1, c2))
        assert res.total == 2
        assert res.met_count == 1
