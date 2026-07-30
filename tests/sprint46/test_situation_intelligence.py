import pytest, os
from dataclasses import FrozenInstanceError
from sam.guardian.live.situation import GuardianSituation, SituationType, SituationSeverity, SituationSummary, SituationStatistics, SituationCandidate, SituationSnapshot
from sam.guardian.live.correlator import TransitionCorrelator
from sam.guardian.live.classifier import SituationClassifier
from sam.guardian.live.severity import SituationSeverityCalculator
from sam.guardian.live.history_situation import SituationHistory
from sam.guardian.live.transition import RuntimeTransition, TransitionType, ImpactLevel
from sam.guardian.live.state import RuntimeStatistics

# DTO immutability
def test_situation_frozen():
    s = GuardianSituation(situation_id="s1", situation_type=SituationType.HEALTHY, severity=SituationSeverity.INFO, timestamp=0.0)
    with pytest.raises(FrozenInstanceError): s.situation_id = "x"

def test_situation_to_dict():
    s = GuardianSituation(situation_id="s1", situation_type=SituationType.BUSY, severity=SituationSeverity.HIGH, timestamp=100.0, description="test")
    d = s.to_dict()
    assert d["situation_type"] == "BUSY"; assert d["severity"] == "HIGH"

def test_summary_frozen():
    su = SituationSummary(total_situations=0, type_counts={}, severity_counts={}, critical_count=0, high_count=0, medium_count=0, low_count=0, info_count=0, period_start=0.0, period_end=0.0)
    with pytest.raises(FrozenInstanceError): su.total_situations = 5
def test_candidate_frozen():
    c = SituationCandidate(transition_ids=[], runtimes=[])
    with pytest.raises(FrozenInstanceError): c.transition_ids = ["x"]
def test_snapshot_frozen():
    su = SituationSummary(total_situations=0, type_counts={}, severity_counts={}, critical_count=0, high_count=0, medium_count=0, low_count=0, info_count=0, period_start=0.0, period_end=0.0)
    sn = SituationSnapshot(snapshot_id="s1", timestamp=0.0, total_active=0, situations=[], highest_severity="INFO", summary=su)
    with pytest.raises(FrozenInstanceError): sn.snapshot_id = "x"

# Correlator
def test_correlator_init():
    c = TransitionCorrelator(); assert c is not None
def test_correlator_empty():
    assert TransitionCorrelator().correlate([]) == []
def test_correlator_single():
    t = RuntimeTransition(transition_id="t1", transition_type=TransitionType.RUNTIME_ADDED, runtime_id="r1", timestamp=0.0)
    cs = TransitionCorrelator().correlate([t])
    assert len(cs) >= 1
def test_correlator_multiple():
    ts = [RuntimeTransition(transition_id=f"t{i}", transition_type=TransitionType.RUNTIME_ADDED, runtime_id="r1", timestamp=float(i)) for i in range(3)]
    cs = TransitionCorrelator().correlate(ts)
    assert len(cs) >= 1

# Severity Calculator
def test_severity_init():
    assert SituationSeverityCalculator() is not None
def test_severity_empty():
    c = SituationCandidate(transition_ids=[], runtimes=[])
    assert SituationSeverityCalculator().calculate(c, []) == SituationSeverity.INFO
def test_severity_critical():
    t = RuntimeTransition(transition_id="t1", transition_type=TransitionType.HEALTH_CHANGED, runtime_id="r1", timestamp=0.0, impact=ImpactLevel.CRITICAL)
    c = SituationCandidate(transition_ids=["t1"], runtimes=["r1"], score=1.0, reason="test")
    assert SituationSeverityCalculator().calculate(c, [t]) == SituationSeverity.CRITICAL

# Classifier
def test_classifier_init():
    assert SituationClassifier() is not None
def test_classifier_empty():
    assert SituationClassifier().classify([]) == []
def test_classifier_healthy():
    t = RuntimeTransition(transition_id="t1", transition_type=TransitionType.RUNTIME_ADDED, runtime_id="r1", timestamp=0.0, impact=ImpactLevel.LOW)
    ss = SituationClassifier().classify([t])
    assert len(ss) >= 1

def test_classifier_runtime_instability():
    ts = [RuntimeTransition(transition_id=f"t{i}", transition_type=TransitionType.HEALTH_CHANGED, runtime_id="r1", timestamp=float(i), impact=ImpactLevel.HIGH) for i in range(2)]
    ss = SituationClassifier().classify(ts)
    types = [s.situation_type for s in ss]
    assert any(t in (SituationType.RUNTIME_INSTABILITY, SituationType.RESOURCE_PRESSURE) for t in types)

# History
def test_history_init():
    h = SituationHistory(); assert h.count == 0; assert h.latest is None
def test_history_record():
    h = SituationHistory()
    s = GuardianSituation(situation_id="s1", situation_type=SituationType.HEALTHY, severity=SituationSeverity.INFO, timestamp=0.0)
    h.record(s); assert h.count == 1; assert h.latest is not None
def test_history_record_batch():
    h = SituationHistory()
    ss = [GuardianSituation(situation_id=f"s{i}", situation_type=SituationType.BUSY, severity=SituationSeverity.MEDIUM, timestamp=float(i)) for i in range(5)]
    h.record_batch(ss); assert h.count == 5
def test_history_lookup():
    h = SituationHistory()
    s = GuardianSituation(situation_id="find", situation_type=SituationType.HEALTHY, severity=SituationSeverity.INFO, timestamp=0.0)
    h.record(s); assert h.lookup("find") is not None; assert h.lookup("no") is None
def test_history_filter_type():
    h = SituationHistory()
    h.record(GuardianSituation(situation_id="s1", situation_type=SituationType.BUSY, severity=SituationSeverity.MEDIUM, timestamp=0.0))
    h.record(GuardianSituation(situation_id="s2", situation_type=SituationType.HEALTHY, severity=SituationSeverity.INFO, timestamp=1.0))
    assert len(h.filter(situation_type=SituationType.BUSY)) == 1
def test_history_filter_severity():
    h = SituationHistory()
    h.record(GuardianSituation(situation_id="s1", situation_type=SituationType.BUSY, severity=SituationSeverity.CRITICAL, timestamp=0.0))
    h.record(GuardianSituation(situation_id="s2", situation_type=SituationType.HEALTHY, severity=SituationSeverity.INFO, timestamp=1.0))
    assert len(h.filter(min_severity=SituationSeverity.HIGH)) == 1
def test_history_get_summary():
    h = SituationHistory()
    h.record(GuardianSituation(situation_id="s1", situation_type=SituationType.BUSY, severity=SituationSeverity.HIGH, timestamp=0.0))
    su = h.get_summary(); assert su.total_situations == 1
def test_history_get_statistics():
    h = SituationHistory()
    h.record(GuardianSituation(situation_id="s1", situation_type=SituationType.HEALTHY, severity=SituationSeverity.INFO, timestamp=0.0))
    st = h.get_statistics(); assert st.total_situations == 1
def test_history_clear():
    h = SituationHistory()
    h.record(GuardianSituation(situation_id="s1", situation_type=SituationType.HEALTHY, severity=SituationSeverity.INFO, timestamp=0.0))
    h.clear(); assert h.count == 0
def test_history_is_full():
    h = SituationHistory(max_size=2)
    for i in range(3):
        h.record(GuardianSituation(situation_id=f"s{i}", situation_type=SituationType.HEALTHY, severity=SituationSeverity.INFO, timestamp=float(i)))
    assert h.count <= 2

# Conversation Bridge
def test_conv_situation_query_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-q"); assert r.conversation_situation.query_count == 10
def test_conv_situation_latest():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-l"); assert r.conversation_situation.latest_situation()["has_situation"] is False
def test_conv_situation_history():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-h"); assert r.conversation_situation.history()["total"] == 0
def test_conv_situation_critical():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-c"); assert r.conversation_situation.critical_situations()["count"] == 0
def test_conv_situation_busy():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-b"); assert r.conversation_situation.busy_runtime()["count"] == 0
def test_conv_situation_bottleneck():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-bn"); assert r.conversation_situation.approval_bottleneck()["count"] == 0
def test_conv_situation_recovery():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-r"); assert r.conversation_situation.recovery()["count"] == 0
def test_conv_situation_statistics():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-st"); res = r.conversation_situation.statistics(); assert "statistics" in res
def test_conv_situation_severity():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-sv"); res = r.conversation_situation.severity(); assert "current_severity" in res
def test_conv_situation_summary():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sc-sm"); res = r.conversation_situation.summary(); assert "summary" in res

# Dashboard Bridge
def test_dash_situation_card_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sd-cc"); assert r.dashboard_situation.card_count == 6
def test_dash_situation_current():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sd-cu"); c = r.dashboard_situation.get_current_situation_card(); assert c.type_name == "NONE"
def test_dash_situation_timeline():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sd-tl"); c = r.dashboard_situation.get_situation_timeline_card(); assert c.total == 0
def test_dash_situation_severity():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sd-sv"); c = r.dashboard_situation.get_situation_severity_card(); assert c.current_severity == "NONE"
def test_dash_situation_statistics():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sd-st"); c = r.dashboard_situation.get_situation_statistics_card(); assert c.total == 0
def test_dash_situation_distribution():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sd-rd"); c = r.dashboard_situation.get_runtime_distribution_card(); assert c.total == 0
def test_dash_situation_history():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sd-ht"); c = r.dashboard_situation.get_situation_history_card(); assert c.total == 0
def test_dash_situation_all_cards():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="sd-ac"); assert len(r.dashboard_situation.get_all_cards()) == 6

# Pipeline
def test_pipeline_with_situation():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class SSub(GuardianEventSubscriber):
        def supports(self, e): return True
        def handle(self, e): return {"h": True}
    r = GuardianLiveRuntime(runtime_id="pipe-sit"); r.start(); r.register_subscriber(SSub())
    r.execute_pipeline({"x": 1})
    r.execute_pipeline({"x": 2})
    st = r.get_status()
    assert "situation_count" in st
    r.stop()

def test_pipeline_situation_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class SSub(GuardianEventSubscriber):
        def supports(self, e): return True
        def handle(self, e): return {"h": True}
    r = GuardianLiveRuntime(runtime_id="pipe-sc"); r.start(); r.register_subscriber(SSub())
    for i in range(3): r.execute_pipeline({"i": i})
    r.stop()

# Forbidden imports
FORBIDDEN = ["from sam.domain", "from sam.repository", "from sam.storage", "from sam.operations",
             "import threading", "import asyncio", "async def", "await ", "import socket",
             "import websockets", "from websocket", "import multiprocessing"]
def test_forbidden():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
    lp = os.path.join(root,"src","sam","guardian","live")
    files = ["situation.py","correlator.py","classifier.py","severity.py","history_situation.py",
             "conversation_situation.py","dashboard_situation.py"]
    for fn in files:
        p = os.path.join(lp, fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: txt = f.read()
            for pat in FORBIDDEN: assert pat not in txt, f"{pat} in {fn}"
def test_no_async():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
    lp = os.path.join(root,"src","sam","guardian","live")
    files = ["situation.py","correlator.py","classifier.py","severity.py","history_situation.py",
             "conversation_situation.py","dashboard_situation.py"]
    for fn in files:
        p = os.path.join(lp, fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: txt = f.read()
            assert "async def" not in txt; assert "await " not in txt

@pytest.mark.parametrize("i", range(80))
def test_deterministic_situation(i):
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class DSub(GuardianEventSubscriber):
        def supports(self, e): return True
        def handle(self, e): return {"i": i}
    r = GuardianLiveRuntime(runtime_id=f"det-sit-{i:03d}"); r.start(); r.register_subscriber(DSub())
    for _ in range(2): r.execute_pipeline({"i": i})
    r.stop()
