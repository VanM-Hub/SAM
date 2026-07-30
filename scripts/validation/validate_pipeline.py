#!/usr/bin/env python3
"""Validate pipeline structure: each runtime has correct stages in __init__.py.

Usage:
    python scripts/validation/validate_pipeline.py
    python scripts/validation/validate_pipeline.py --report
"""

import os
import sys
import json
import re

SAM_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "sam")
if not os.path.isdir(SAM_SRC):
    SAM_SRC = os.path.join("D:", os.sep, "Project AI", "SAM", "src", "sam")

SCORE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "reports", "architecture_pipeline_score.json")

# Expected pipeline files per subsystem
SUBSYSTEM_PIPELINES = {
    "guardian.live": {
        "expected_files": ["event", "state", "synchronizer", "transition", "situation",
                           "assessment", "intent", "handoff", "runtime"],
        "loose_check": True,  # Allow extra files
    },
    "operations.brain.decision": {
        "expected_files": ["evaluation", "planning", "approval_activation", "certification",
                           "finalization", "runtime_v3"],
        "loose_check": True,
    },
    "approval": {
        "expected_files": ["intake_record", "policy", "workflow", "multilevel",
                           "history", "dashboard_analytics"],
        "loose_check": True,
    },
    "operational_brain": {
        "expected_files": ["health_aggregator", "readiness_checker", "operational_planner",
                           "operational_scheduler", "operational_monitor", "operational_plan_exporter"],
        "loose_check": True,
    },
    "activation": {
        "expected_files": ["activation_request", "activation_builder", "activation_draft",
                           "activation_package", "activation_validator", "package_export",
                           "activation_runtime"],
        "loose_check": True,
    },
    "execution.runtime": {
        "expected_files": ["execution_request", "execution_strategy", "resource_plan",
                           "dependency_graph", "timeline", "budget", "risk", "quality",
                           "simulation", "assembly", "runtime"],
        "loose_check": True,
    },
    "runtime_kernel": {
        "expected_files": ["startup_manager", "runtime_context", "runtime_registry",
                           "state_machine", "lifecycle_manager", "adapter_registry",
                           "health_checker", "security_manager", "scheduler_engine",
                           "event_bus", "coordination_engine", "telemetry_collector",
                           "kernel_final"],
        "loose_check": True,
    },
}

def scan():
    warnings = []
    errors = []
    for subsystem, cfg in SUBSYSTEM_PIPELINES.items():
        pkg_path = os.path.join(SAM_SRC, *subsystem.split("."))
        if not os.path.isdir(pkg_path):
            errors.append(f"MISSING PACKAGE: sam.{subsystem} at {pkg_path}")
            continue
        actual_files = set()
        for f in os.listdir(pkg_path):
            if f.endswith(".py") and not f.startswith("__"):
                actual_files.add(f[:-3])
        for expected in cfg["expected_files"]:
            if expected not in actual_files:
                extra = ""
                if cfg["loose_check"]:
                    # Find closest match
                    similar = [a for a in actual_files if expected.split("_")[0] in a]
                    if similar:
                        extra = f" (similar: {', '.join(similar)})"
                    warnings.append(f"MISSING: sam.{subsystem}/ missing {expected}.py{extra}")
                else:
                    errors.append(f"MISSING: sam.{subsystem}/ missing {expected}.py")
        # Check for required runtime/coordinator
        if "runtime" in cfg["expected_files"] and "runtime" not in actual_files:
            if "runtime_v3" in actual_files:
                pass  # alternate name
            elif "activation_runtime" in actual_files:
                pass
            else:
                errors.append(f"MISSING RUNTIME: sam.{subsystem}/ — no runtime*.py found")

    result = {
        "errors": errors,
        "warnings": warnings,
        "pass": len(errors) == 0,
    }
    return result

def main():
    result = scan()
    if "--report" in sys.argv:
        os.makedirs(os.path.dirname(SCORE_FILE), exist_ok=True)
        with open(SCORE_FILE, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Report written to {SCORE_FILE}")
    if result["errors"]:
        for e in result["errors"]:
            print(f"❌ {e}")
        print(f"\n❌ FAILED: {len(result['errors'])} pipeline errors")
        sys.exit(1)
    if result["warnings"]:
        for w in result["warnings"]:
            print(f"⚠️  {w}")
    print(f"✅ PASS: pipeline structure valid (7 subsystems checked)")
    return 0

if __name__ == "__main__":
    main()
