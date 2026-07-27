"""Soak test script for SAM RC3.

Simulates continuous workload for stability testing.
Logs to: logs/soak_test_<timestamp>.log
Run: python scripts/soak_test.py
"""
import asyncio
import time
import os
import sys
import logging
import datetime

# Setup log file
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"soak_test_{timestamp}.log"
log_path = os.path.join(log_dir, log_filename)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("soak_test")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["SAM_DB_PATH"] = "sam_soak_test.db"


class SoakTestMonitor:
    """Monitors SAM stability over time."""

    def __init__(self):
        self.start_time = time.time()
        self.workflow_count = 0
        self.error_count = 0
        self.memory_samples = []
        self.cpu_samples = []

    async def _get_db(self):
        """Get a Database instance for tests that need persistence."""
        from sam.persistence.database import Database
        db_path = os.environ.get("SAM_DB_PATH", "sam_soak_test.db")
        db = Database(db_path)
        await db.initialize()
        return db

    async def _make_cognitive_state_manager(self):
        """Create a bare CognitiveStateManager (zero deps)."""
        from sam.cognition.state import CognitiveStateManager
        return CognitiveStateManager()

    async def _make_working_memory(self):
        """Create a bare WorkingMemoryManager (zero deps)."""
        from sam.cognition.memory import WorkingMemoryManager
        return WorkingMemoryManager()

    async def run_diagnose(self):
        try:
            from sam.cognition.manager import CognitiveManager
            state_mgr = await self._make_cognitive_state_manager()
            wm = await self._make_working_memory()
            mgr = CognitiveManager(state_manager=state_mgr, working_memory_manager=wm)
            state = await mgr.get_current_state()
            logger.info("diagnose_ok: health=%.1f focus=%s",
                        getattr(state, 'health', 100.0),
                        getattr(state, 'focus', 'balanced'))
            return True
        except Exception as e:
            logger.error("diagnose_failed: %s", e)
            self.error_count += 1
            return False

    async def run_reflection(self):
        try:
            from sam.healing.reflection import ReflectionManager
            db = await self._get_db()
            ref = ReflectionManager(db=db)
            count = await ref.get_reflection_count()
            logger.info("reflection_ok: reflections=%d", count)
            return True
        except Exception as e:
            # Fallback: try with lessons_summary
            try:
                from sam.healing.reflection import ReflectionManager
                db = await self._get_db()
                ref = ReflectionManager(db=db)
                summary = await ref.get_lessons_summary()
                logger.info("reflection_ok: lessons_summary=%d items", len(summary))
                return True
            except Exception as e2:
                logger.error("reflection_failed: %s", e2)
                self.error_count += 1
                return False

    async def run_autonomy_status(self):
        try:
            from sam.autonomy.controller import AutonomyController
            ctrl = AutonomyController()
            level = await ctrl.get_current_level()
            logger.info("autonomy_ok: level=%s", level.value)
            return True
        except Exception as e:
            logger.error("autonomy_failed: %s", e)
            self.error_count += 1
            return False

    async def run_evolution_check(self):
        """Check evolution subsystem with proper dependency injection."""
        try:
            from sam.persistence.database import Database
            from sam.evolution.params import ParamManager, OptimizableParam
            from sam.institutional.memory import InstitutionalMemoryManager

            db = await self._get_db()
            param_mgr = ParamManager(db=db)

            # Test basic param creation (does not require SelfOptimizer)
            p = OptimizableParam(id="test", name="test-param", current_value=50)
            logger.info("evolution_ok: param=%s value=%s", p.name, p.current_value)

            # Also test ParamManager
            await param_mgr.register_defaults()
            all_params = await param_mgr.list()
            logger.info("evolution_ok: params_registered=%d", len(all_params))
            return True
        except Exception as e:
            logger.error("evolution_failed: %s", e)
            self.error_count += 1
            return False

    async def run_attention_check(self):
        """Check attention subsystem with proper dependency injection."""
        try:
            from sam.cognition.attention import AttentionManager
            from sam.cognition.state import CognitiveStateManager
            from sam.cognition.memory import WorkingMemoryManager

            state_mgr = await self._make_cognitive_state_manager()
            wm = await self._make_working_memory()

            attn = AttentionManager(
                cognitive_state_manager=state_mgr,
                working_memory=wm,
            )
            profile = await attn.get_current_profile()
            logger.info("attention_ok: focus=%s conf=%.1f",
                        profile.primary_focus.value if profile else "balanced",
                        profile.confidence if profile else 1.0)
            return True
        except Exception as e:
            logger.error("attention_failed: %s", e)
            self.error_count += 1
            return False

    async def run_autonomy_level_check(self):
        try:
            from sam.autonomy.assessment import SelfAssessment
            assess = SelfAssessment()
            result = await assess.assess_before({})
            logger.info("assessment_ok: risk=%.1f",
                        getattr(result, 'risk_score', 0.0))
            return True
        except Exception as e:
            logger.error("assessment_failed: %s", e)
            self.error_count += 1
            return False

    def record_metrics(self):
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem = process.memory_info().rss / 1024 / 1024
            cpu = process.cpu_percent(interval=0.1)
        except Exception:
            mem = 0
            cpu = 0
        self.memory_samples.append(mem)
        self.cpu_samples.append(cpu)
        elapsed = time.time() - self.start_time
        logger.info(
            "metrics: elapsed=%.1fh mem=%.1fMB cpu=%.1f%% workflows=%d errors=%d",
            elapsed / 3600, mem, cpu, self.workflow_count, self.error_count,
        )

    def summary(self):
        elapsed = time.time() - self.start_time
        lines = []
        lines.append("=" * 60)
        lines.append("SAM Soak Test Summary")
        lines.append("=" * 60)
        lines.append(f"  Duration : {elapsed:.0f}s ({elapsed/3600:.1f}h)")
        lines.append(f"  Workflows: {self.workflow_count}")
        lines.append(f"  Errors   : {self.error_count}")
        if self.memory_samples:
            avg_mem = sum(self.memory_samples) / len(self.memory_samples)
            lines.append(f"  Memory   : min={min(self.memory_samples):.1f} max={max(self.memory_samples):.1f} avg={avg_mem:.1f} MB")
        if self.cpu_samples:
            avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples)
            lines.append(f"  CPU      : min={min(self.cpu_samples):.1f} max={max(self.cpu_samples):.1f} avg={avg_cpu:.1f} %")
        if self.error_count > 0:
            lines.append(f"  \u26a0\ufe0f  {self.error_count} errors detected!")
        else:
            lines.append("  \u2705 No errors detected!")
        lines.append("=" * 60)
        summary_text = "\n".join(lines)
        logger.info("\n" + summary_text)
        print("\n" + summary_text)


async def main():
    monitor = SoakTestMonitor()
    interval_diagnose = 300
    interval_reflection = 600
    interval_autonomy = 900
    interval_metrics = 60

    logger.info("soak_test_started: diagnose=%ds reflection=%ds autonomy=%ds",
                interval_diagnose, interval_reflection, interval_autonomy)

    last_diagnose = 0
    last_reflection = 0
    last_autonomy = 0
    last_evolution = 0
    last_attention = 0

    try:
        while True:
            now = time.time()

            # Diagnose every 5 min
            if now - last_diagnose >= interval_diagnose:
                await monitor.run_diagnose()
                monitor.workflow_count += 1
                last_diagnose = now

            # Reflection every 10 min
            if now - last_reflection >= interval_reflection:
                await monitor.run_reflection()
                last_reflection = now

            # Autonomy + evolution + attention every 15 min
            if now - last_autonomy >= interval_autonomy:
                await monitor.run_autonomy_status()
                await monitor.run_evolution_check()
                await monitor.run_attention_check()
                last_autonomy = now

            # Metrics every 1 min
            if int(now) % interval_metrics < 5:
                monitor.record_metrics()

            await asyncio.sleep(5)

    except KeyboardInterrupt:
        logger.info("soak_test_stopped by user")
        monitor.summary()
    except Exception as e:
        logger.error("soak_test_crashed: %s", e)
        monitor.summary()


if __name__ == "__main__":
    print("SAM RC3 Soak Test")
    print("=" * 60)
    print(f"Log file: {log_path}")
    print("Running... Press Ctrl+C to stop")
    asyncio.run(main())
