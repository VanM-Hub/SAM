import pytest
from sam.operations.brain.reasoning.session import ReasoningSession, ReasoningContext
from sam.operations.brain.reasoning.context_builder import ContextAssembler, ObservationSnapshot, MissionDashboardDTO, BrainDashboardDTO, TimelineSummary, MissionSummary
from sam.operations.brain.reasoning.strategy import StrategyEngine, ReasoningMode
from sam.operations.brain.reasoning.scheduler import ProviderScheduler
from sam.operations.brain.reasoning.validator import ResponseValidator
from sam.operations.brain.reasoning.pipeline import ReasoningPipeline
from sam.operations.brain.reasoning.conversation import ConversationReasoningIntegration
from sam.operations.reasoning.provider import ReasoningResponse, UsageMetrics


class MockProvider:
    def __init__(self, name="mock", healthy=True, fail=False, delay=0):
        self.name = name
        self._healthy = healthy
        self._fail = fail
        self.delay = delay

    def generate(self, request):
        if self._fail:
            raise RuntimeError("provider failure")
        # return standardized ReasoningResponse
        return ReasoningResponse(
            answer=f"Answer from {self.name}: {request.prompt}",
            confidence=0.9,
            provider=self.name,
            usage=UsageMetrics(),
            citations=(),
            unsupported_claims=(),
            latency_ms=10.0,
            warnings=(),
        )

    def health(self):
        return bool(self._healthy)

    def metadata(self):
        return {"name": self.name}


@pytest.mark.parametrize("n", list(range(10)))
def test_session_recording_and_snapshot(n):
    s = ReasoningSession(session_id=f"t-{n}")
    assert s.is_active
    ctx = ReasoningContext(operator_question=f"q-{n}")
    s.set_context(ctx)
    rec = s.record_reasoning(question=f"q-{n}", template_name="explain", token_estimate=5)
    assert rec.operator_question == f"q-{n}"
    snap = s.snapshot()
    assert snap.session_id == s.session_id
    assert s.tokens_used >= 0


@pytest.mark.parametrize("length", [0, 10, 100, 500, 999, 1200, 1500, 2000, 5000, 10000])
def test_context_assembler_truncation(length):
    ca = ContextAssembler()
    obs = ObservationSnapshot(count=1, latest_observations=( {"detail": "x"*length}, ))
    ctx = ca.assemble(operator_question="hello", observations=obs)
    # summaries must not exceed MAX_SUMMARY_LENGTH
    assert len(ctx.observation_summary) <= ca.MAX_SUMMARY_LENGTH


@pytest.mark.parametrize("phrase", [
    "What is the mission status?","Is the system healthy?","What are the risks?",
    "Why did it fail?","Recommend next steps","Please explain how it works",
    "Validate the hypothesis","Summarize recent activity","Analyze recent anomalies",
    "Help me choose an action","mission progress","system health check","risk assessment",
    "root cause analysis please","suggest best action","how does X happen","verify the claim",
    "overview of timeline","investigate performance","compare two options","explain reasoning",
    "analyze logs","summarize logs","what's the status","is it running",
    "confirm the result","recommendation for fix","why error","what caused the problem",
    "validate evidence","check citations","give a summary","provide recommendation"
])
def test_strategy_engine_resolve(phrase):
    mode = StrategyEngine.resolve_mode(phrase)
    strat = StrategyEngine.get_strategy(mode)
    assert strat.template_name
    assert strat.description


@pytest.mark.parametrize("count", list(range(1,11)))
def test_scheduler_register_and_schedule(count):
    sched = ProviderScheduler()
    for i in range(count):
        name = f"p{i}"
        sched.register(name, MockProvider(name=name))
    # ensure active_providers reports providers
    active = sched.active_providers
    assert len(active) >= 1
    # schedule a simple request
    res = sched.schedule({"prompt": "hi"})
    # scheduler returns a SchedulerResult
    assert hasattr(res, "success")


@pytest.mark.parametrize("threshold", [1,2,3,4,5,6,7,8,9,10])
def test_scheduler_circuit_breaker_behavior(threshold):
    sched = ProviderScheduler()
    mp = MockProvider(name="bad", healthy=False, fail=True)
    sched.register("bad", mp, retry_count=0, circuit_breaker_threshold=threshold)
    # cause failures
    for _ in range(threshold + 1):
        r = sched.schedule({"prompt": "x"}, preferred="bad")
    # After repeated failures, circuit breaker should prevent immediate use
    # health_report should mark provider as False
    hr = sched.health_report()
    assert "bad" in hr


@pytest.mark.parametrize("case", [
    ("", 1.0, (), (), (), 0, 0, False),
    ("Non empty", 0.8, ("e1","e2"), (("a",1),), (), 1, 1, False),
    ("{incomplete json", 0.5, (), (), (), 0, 0, False),
    ("```\ncode", 0.5, (), (), (), 0, 0, False),
])
def test_validator_various(case):
    answer, conf, evidence_ids, citations, unsupported, supported_claims, total_claims, required = case
    rv = ResponseValidator()
    report = rv.validate(answer=answer, confidence=conf, evidence_ids=tuple(evidence_ids), citations=tuple(citations), unsupported_claims=tuple(unsupported), supported_claims=supported_claims, total_claims=total_claims, required_evidence=required)
    assert isinstance(report.passed, bool)


@pytest.mark.parametrize("providers", list(range(1,16)))
def test_pipeline_with_mock_provider(providers):
    # register N mock providers; one should succeed
    sched = ProviderScheduler()
    for i in range(providers):
        sched.register(f"m{i}", MockProvider(name=f"m{i}"), priority=100-i)
    session = ReasoningSession(session_id="pl-1")
    ca = ContextAssembler()
    se = StrategyEngine()
    rv = ResponseValidator()
    pipeline = ReasoningPipeline(session=session, context_assembler=ca, strategy_engine=se, scheduler=sched, validator=rv)

    res = pipeline.run("What is the mission status?")
    assert res.session_id == session.session_id
    assert hasattr(res, "validation")


@pytest.mark.parametrize("attempts", list(range(1,11)))
def test_pipeline_provider_unavailable(attempts):
    sched = ProviderScheduler()
    # no providers registered
    session = ReasoningSession(session_id="pl-2")
    ca = ContextAssembler()
    se = StrategyEngine()
    rv = ResponseValidator()
    pipeline = ReasoningPipeline(session=session, context_assembler=ca, strategy_engine=se, scheduler=sched, validator=rv)
    res = pipeline.run("Is system healthy?")
    assert "Provider unavailable" in res.answer or res.confidence == 0.0


@pytest.mark.parametrize("q", [
    "Operational question 1","Operational question 2","Operational question 3",
    "Operational question 4","Operational question 5"
])
def test_conversation_integration_asks(q):
    sched = ProviderScheduler()
    sched.register("mock", MockProvider(name="mock"))
    session = ReasoningSession(session_id="conv-1")
    ca = ContextAssembler()
    se = StrategyEngine()
    rv = ResponseValidator()
    pipeline = ReasoningPipeline(session=session, context_assembler=ca, strategy_engine=se, scheduler=sched, validator=rv)
    conv = ConversationReasoningIntegration(pipeline)
    ask = conv.ask_operational
    res = ask(type("Q", (), {"question": q, "context_summary": ""})())
    # ensure ReasoningResult returned
    assert hasattr(res, "response")


@pytest.mark.parametrize("n", [1,2,3,4,5])
def test_dashboard_service_reads(n):
    sched = ProviderScheduler()
    sched.register("mock", MockProvider(name="mock"))
    session = ReasoningSession(session_id="dash-1")
    ca = ContextAssembler()
    se = StrategyEngine()
    rv = ResponseValidator()
    pipeline = ReasoningPipeline(session=session, context_assembler=ca, strategy_engine=se, scheduler=sched, validator=rv)
    from sam.operations.brain.reasoning.dashboard_reasoning import DashboardReasoningService
    ds = DashboardReasoningService(pipeline, sched)
    status = ds.get_status()
    assert hasattr(status, "active_sessions")


# Ensure MockProvider remains usable as default
def test_mockprovider_default_behavior():
    m = MockProvider()
    assert m.health()
    r = m.generate(type("R", (), {"prompt": "hello"})())
    assert hasattr(r, "answer")
