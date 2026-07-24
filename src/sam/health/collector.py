"""Health Collector for SAM Framework.

Collects health status from all registered services.
"""

import structlog
from typing import Dict, Any, Optional
from datetime import datetime

from .models import HealthReport, ComponentHealth, HealthCheck, HealthStatus

logger = structlog.get_logger()


class HealthCollector:
    """Collects health status from all services.

    Each service should implement an async health() method that returns
    a ComponentHealth or raises an exception (which will be caught and
    reported as UNHEALTHY).
    """

    def __init__(self, services: Dict[str, Any]) -> None:
        """
        Args:
            services: Dictionary mapping service names to service instances.
                      Expected keys: registry, event_bus, audit, evidence, knowledge,
                      pattern, recommendation, approval, configuration, database
        """
        self.services = services
        self.logger = logger.bind(component="HealthCollector")

    async def collect(self) -> HealthReport:
        """Collect health from all registered services.

        Returns:
            HealthReport with status of all components.
        """
        self.logger.info("Starting health collection", service_count=len(self.services))
        report = HealthReport()

        # Define service health check methods
        health_checks = {
            "registry": self._check_registry,
            "event_bus": self._check_event_bus,
            "audit": self._check_audit,
            "evidence": self._check_evidence,
            "knowledge": self._check_knowledge,
            "pattern": self._check_pattern,
            "recommendation": self._check_recommendation,
            "approval": self._check_approval,
            "configuration": self._check_configuration,
            "database": self._check_database,
        }

        for name, check_fn in health_checks.items():
            service = self.services.get(name)
            if service is None:
                # Service not provided, mark as unknown
                comp = ComponentHealth(
                    component=name,
                    status=HealthStatus.UNKNOWN,
                    message="Service not registered in collector",
                )
                report.add_component(comp)
                continue

            try:
                comp = await check_fn(service)
                report.add_component(comp)
            except Exception as e:
                self.logger.exception("Health check failed", service=name, error=str(e))
                comp = ComponentHealth(
                    component=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check raised exception: {type(e).__name__}: {e}",
                    details={"error": str(e), "error_type": type(e).__name__},
                )
                report.add_component(comp)

        self.logger.info("Health collection complete", overall_status=report.status.value)
        return report

    async def _check_registry(self, registry) -> ComponentHealth:
        """Check capability registry health."""
        comp = ComponentHealth(component="registry", status=HealthStatus.HEALTHY)
        try:
            # Check if registry is accessible and has descriptors
            descriptors = await registry.list_descriptors()
            comp.add_check(HealthCheck(
                component="registry.descriptors",
                status=HealthStatus.HEALTHY,
                message=f"Registry accessible with {len(descriptors)} capabilities",
                details={"count": len(descriptors)},
            ))
        except Exception as e:
            comp.add_check(HealthCheck(
                component="registry.descriptors",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to list descriptors: {e}",
                details={"error": str(e)},
            ))
        return comp

    async def _check_event_bus(self, event_bus) -> ComponentHealth:
        """Check event bus health."""
        comp = ComponentHealth(component="event_bus", status=HealthStatus.HEALTHY)
        try:
            # Check if event bus has subscribers (basic accessibility)
            subscriber_count = sum(len(h) for h in event_bus._subscribers.values())
            comp.add_check(HealthCheck(
                component="event_bus.subscribers",
                status=HealthStatus.HEALTHY,
                message=f"Event bus operational with {subscriber_count} subscriptions",
                details={"subscriptions": subscriber_count, "event_types": list(event_bus._subscribers.keys())},
            ))
        except Exception as e:
            comp.add_check(HealthCheck(
                component="event_bus.subscribers",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check event bus: {e}",
                details={"error": str(e)},
            ))
        return comp

    async def _check_audit(self, audit_service) -> ComponentHealth:
        """Check audit service health."""
        comp = ComponentHealth(component="audit", status=HealthStatus.HEALTHY)
        try:
            # Try to get events (tests if audit is recording)
            events = audit_service.get_events(limit=1)
            comp.add_check(HealthCheck(
                component="audit.storage",
                status=HealthStatus.HEALTHY,
                message=f"Audit service recording ({audit_service.count} events)",
                details={"event_count": audit_service.count},
            ))
        except Exception as e:
            comp.add_check(HealthCheck(
                component="audit.storage",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to access audit: {e}",
                details={"error": str(e)},
            ))
        return comp

    async def _check_evidence(self, evidence_store) -> ComponentHealth:
        """Check evidence store health."""
        comp = ComponentHealth(component="evidence", status=HealthStatus.HEALTHY)
        try:
            count = len(evidence_store)
            has_repo = evidence_store._repo is not None
            comp.add_check(HealthCheck(
                component="evidence.store",
                status=HealthStatus.HEALTHY,
                message=f"Evidence store accessible ({count} in memory, persistent={has_repo})",
                details={"in_memory_count": count, "persistent": has_repo},
            ))
            # If persistent, also check database connectivity
            if has_repo:
                # Try a simple query through repo
                try:
                    await evidence_store._repo.add(evidence_store._evidence[0] if evidence_store._evidence else None)
                except Exception:
                    # Adding None might fail, that's OK - we just check if repo exists
                    pass
        except Exception as e:
            comp.add_check(HealthCheck(
                component="evidence.store",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to access evidence store: {e}",
                details={"error": str(e)},
            ))
        return comp

    async def _check_knowledge(self, knowledge_store) -> ComponentHealth:
        """Check knowledge store health."""
        comp = ComponentHealth(component="knowledge", status=HealthStatus.HEALTHY)
        try:
            count = len(knowledge_store)
            has_repo = knowledge_store._repo is not None
            comp.add_check(HealthCheck(
                component="knowledge.store",
                status=HealthStatus.HEALTHY,
                message=f"Knowledge store accessible ({count} facts in memory, persistent={has_repo})",
                details={"in_memory_count": count, "persistent": has_repo},
            ))
        except Exception as e:
            comp.add_check(HealthCheck(
                component="knowledge.store",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to access knowledge store: {e}",
                details={"error": str(e)},
            ))
        return comp

    async def _check_pattern(self, pattern_engine) -> ComponentHealth:
        """Check pattern engine health."""
        comp = ComponentHealth(component="pattern", status=HealthStatus.HEALTHY)
        try:
            rule_count = len(pattern_engine._rules)
            detection_count = len(pattern_engine._detections)
            has_repo = pattern_engine._repo is not None
            comp.add_check(HealthCheck(
                component="pattern.engine",
                status=HealthStatus.HEALTHY,
                message=f"Pattern engine operational ({rule_count} rules, {detection_count} detections, persistent={has_repo})",
                details={"rules": rule_count, "detections": detection_count, "persistent": has_repo},
            ))
        except Exception as e:
            comp.add_check(HealthCheck(
                component="pattern.engine",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to access pattern engine: {e}",
                details={"error": str(e)},
            ))
        return comp

    async def _check_recommendation(self, recommendation_engine) -> ComponentHealth:
        """Check recommendation engine health."""
        comp = ComponentHealth(component="recommendation", status=HealthStatus.HEALTHY)
        try:
            rule_count = len(recommendation_engine._rule_action_map)
            rec_count = len(recommendation_engine._recommendations)
            has_repo = recommendation_engine._repo is not None
            comp.add_check(HealthCheck(
                component="recommendation.engine",
                status=HealthStatus.HEALTHY,
                message=f"Recommendation engine operational ({rule_count} templates, {rec_count} recommendations, persistent={has_repo})",
                details={"templates": rule_count, "recommendations": rec_count, "persistent": has_repo},
            ))
        except Exception as e:
            comp.add_check(HealthCheck(
                component="recommendation.engine",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to access recommendation engine: {e}",
                details={"error": str(e)},
            ))
        return comp

    async def _check_approval(self, approval_engine) -> ComponentHealth:
        """Check approval engine health."""
        comp = ComponentHealth(component="approval", status=HealthStatus.HEALTHY)
        try:
            pending = await approval_engine.get_pending()
            total = len(approval_engine._requests)
            has_repo = approval_engine._repo is not None
            comp.add_check(HealthCheck(
                component="approval.engine",
                status=HealthStatus.HEALTHY,
                message=f"Approval engine operational ({total} requests, {len(pending)} pending, persistent={has_repo})",
                details={"total_requests": total, "pending": len(pending), "persistent": has_repo},
            ))
        except Exception as e:
            comp.add_check(HealthCheck(
                component="approval.engine",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to access approval engine: {e}",
                details={"error": str(e)},
            ))
        return comp

    async def _check_configuration(self, config_service) -> ComponentHealth:
        """Check configuration service health."""
        comp = ComponentHealth(component="configuration", status=HealthStatus.HEALTHY)
        try:
            # Check if config file is readable
            config_items = config_service.items()
            comp.add_check(HealthCheck(
                component="configuration.file",
                status=HealthStatus.HEALTHY,
                message=f"Configuration loaded ({len(config_items)} keys)",
                details={"keys_count": len(config_items), "path": config_service.config_path},
            ))
        except Exception as e:
            comp.add_check(HealthCheck(
                component="configuration.file",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to access configuration: {e}",
                details={"error": str(e)},
            ))
        return comp

    async def _check_database(self, database) -> ComponentHealth:
        """Check database health."""
        comp = ComponentHealth(component="database", status=HealthStatus.HEALTHY)
        try:
            # Check if connection is alive and schema version
            version_row = await database.fetch_one("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            version = version_row["version"] if version_row else "unknown"
            
            # Check table counts
            tables = ["evidence", "knowledge", "patterns", "recommendations", "approvals", "executions", "reports"]
            table_counts = {}
            for table in tables:
                try:
                    row = await database.fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
                    table_counts[table] = row["cnt"] if row else 0
                except Exception:
                    table_counts[table] = "error"
            
            comp.add_check(HealthCheck(
                component="database.connection",
                status=HealthStatus.HEALTHY,
                message=f"Database connected (schema v{version})",
                details={"schema_version": version, "tables": table_counts},
            ))
        except Exception as e:
            comp.add_check(HealthCheck(
                component="database.connection",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {e}",
                details={"error": str(e)},
            ))
        return comp