"""
SAM Operations CLI — Entry point tanpa dependensi legacy.
Semua output pakai teks ASCII/UTF-8 aman untuk Windows console.

Semua user-facing language berasal dari Narrative Engine.
"""

import sys
import os
import argparse

src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def _get_engine():
    """Buat ExperienceEngine dengan Narrative."""
    from sam.experience.engine import ExperienceEngine
    from sam.telemetry.service import TelemetryService
    svc = TelemetryService()
    return ExperienceEngine(svc)


def cmd_briefing(args):
    """Narrative: Daily Briefing."""
    engine = _get_engine()
    brief = engine.build_daily_briefing()

    print()
    print(brief.greeting)
    print(brief.health_summary)
    print()
    if brief.yesterday_recap and "No significant" not in brief.yesterday_recap:
        print("Recent activity:")
        for line in brief.yesterday_recap.split("\n"):
            print("  " + line)
        print()
    print(brief.action_summary)
    print()
    if brief.schedule:
        print("Today's scheduled work:")
        for s in brief.schedule:
            print("  " + s)
        print()


def cmd_situation(args):
    """Narrative: Current Situation."""
    engine = _get_engine()
    sit = engine.build_situation_brief()

    print()
    print(sit.summary)
    print("  " + sit.health_statement)
    print("  " + sit.knowledge_statement)
    print("  " + sit.incident_statement)
    print("  " + sit.work_statement)
    print()


def cmd_home(args):
    """Narrative: Home narrative bundle."""
    engine = _get_engine()
    bundle = engine.build_narrative_home()

    print()
    if bundle.primary:
        print(bundle.primary.title)
        if bundle.primary.details:
            print("  " + bundle.primary.details)
        print()

    for n in bundle.supporting:
        if n.importance.value in ("action_required", "attention"):
            marker = "!" if n.action_required else "i"
            print("[{}] {}".format(marker, n.title))
            if n.recommended_action:
                print("    -> " + n.recommended_action)
            print()

    if bundle.action_count == 0:
        print("No action required.")
        print()


def cmd_activity(args):
    """Narrative: Activity narrative."""
    engine = _get_engine()
    narratives = engine.build_narrative_activity()

    print()
    if narratives:
        for n in narratives[:5]:
            print("  \u2022 {}".format(n.summary))
    else:
        model = engine.build_activity()
        if model.groups:
            for entry in model.groups[0].entries[:5]:
                print("  {}  {}".format(entry.time, entry.description))
    print()


def cmd_work(args):
    """Narrative: Work narrative."""
    engine = _get_engine()
    narratives = engine.build_narrative_work()

    print()
    if narratives:
        for n in narratives:
            print("  " + n.title)
            if n.details:
                print("    " + n.details)
            if n.recommended_action:
                print("    -> " + n.recommended_action)
            print()
    else:
        model = engine.build_work()
        if model.items:
            for w in model.items[:5]:
                marker = "[W]"
                if w.approval_needed:
                    marker = "[!]"
                print("  {} {} - {}".format(marker, w.title, w.status))
        else:
            print("  No active work.")
            print()
    print()


def cmd_approvals(args):
    """Narrative: Pending approvals."""
    from sam.operations.engine.task import TaskEngine
    from sam.telemetry.service import TelemetryService

    engine = _get_engine()
    narratives = engine.build_narrative_work()

    print()
    approvals = [n for n in narratives if n.narrative_type.value == "approval_needed"]
    if approvals:
        for a in approvals:
            print("  \u26a0\ufe0f {}".format(a.title))
            if a.estimated_time:
                print("    Estimated: {}".format(a.estimated_time))
            if a.estimated_impact:
                print("    Impact: {}".format(a.estimated_impact))
            print()
    else:
        print("  No pending approvals.")
        print()


def cmd_knowledge(args):
    """Narrative: System Knowledge."""
    engine = _get_engine()
    narratives = engine.build_narrative_knowledge()

    print()
    if narratives:
        for n in narratives:
            marker = "\U0001f4a1" if n.importance.value == "attention" else "\U0001f4cc"
            conf = ""
            if n.confidence:
                conf = " ({:.0f}% confidence)".format(n.confidence * 100)
            print("  {} {}{}".format(marker, n.title, conf))
        print()
    else:
        model = engine.build_knowledge()
        if model.items:
            for item in model.items[:5]:
                print("  - {}".format(item.title))
        else:
            print("  No knowledge recorded yet.")
        print()


def cmd_history(args):
    """History narrative (maintain backward compat)."""
    from sam.operations.engine.history import HistoryEngine
    from sam.telemetry.service import TelemetryService

    engine = _get_engine()
    model = engine.build_history()

    print()
    if model.stories:
        for story in model.stories[:5]:
            print("[{}]".format(story.label))
            for event in story.events[:10]:
                print("  \u2022 {}".format(event))
            print()
    else:
        print("  No history recorded.")
        print()


def cmd_settings(args):
    """Settings display."""
    from sam.operations.engine.settings import SettingsEngine

    engine = SettingsEngine()
    model = engine.get_settings()

    print()
    for section in model.sections:
        print("[{}]".format(section.name))
        for item in section.items:
            print("  {}: {}".format(item.key, item.value))
        print()


def cmd_ask(args):
    """Question Engine — Conversation. Antarmuka manusia pertama."""
    engine = _get_engine()
    question = " ".join(args.extra) if args.extra else ""

    if not question:
        # Interactive mode
        print()
        print("SAM — Ask anything about the system.")
        print("(Type 'exit' to quit)")
        print()
        while True:
            try:
                q = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not q or q.lower() in ("exit", "quit", "q"):
                break
            answer = engine.get_live_answer(q)
            print()
            print(answer.display_cli())
            print()
        return

    answer = engine.get_live_answer(question)
    print()
    print(answer.display_cli())
    print()


def main():
    parser = argparse.ArgumentParser(description="SAM Operations CLI")
    parser.add_argument("command",
                        choices=["briefing", "situation", "home",
                                 "activity", "work", "approvals",
                                 "knowledge", "history", "settings",
                                 "ask"],
                        help="Command — semua narrative-aware")
    parser.add_argument("extra", nargs=argparse.REMAINDER,
                        help="Additional arguments (for ask)")

    parsed = parser.parse_args()

    commands = {
        "briefing": cmd_briefing,
        "situation": cmd_situation,
        "home": cmd_home,
        "activity": cmd_activity,
        "work": cmd_work,
        "approvals": cmd_approvals,
        "knowledge": cmd_knowledge,
        "history": cmd_history,
        "settings": cmd_settings,
        "ask": cmd_ask,
    }

    cmd_fn = commands.get(parsed.command)
    if cmd_fn:
        cmd_fn(parsed)


if __name__ == "__main__":
    main()
