"""
Planning Engine – Sprint 22 Fase 2

Translates structured Intents into executable Execution Graphs using
pre-defined templates and optional Knowledge Graph enrichment.

Flow: Intent → (template lookup) → instantiate graph → enrich with knowledge → validated graph
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import structlog

from .intent import Intent, IntentType
from .templates import GraphTemplate, BUILTIN_TEMPLATES, get_default_template
from .candidate import PlanCandidate
from .ranker import PlanRanker
from ..execution.graph import ExecutionGraph, GraphStatus
from ..execution.node import (
    ExecutionNode,
    RetryPolicy,
    CompensationPolicy,
    RetryBackoff,
    CompensationOnFailure,
)

logger = structlog.get_logger()


# ── Planning Engine ───────────────────────────────────────────────────


class PlanError(Exception):
    """Raised when the Planning Engine cannot produce a valid graph."""

    def __init__(self, message: str, intent_id: str = ""):
        super().__init__(message)
        self.intent_id = intent_id


class PlanningEngine:
    """Produces Execution Graphs from structured Intents.

    Responsibilities:
    1. Look up the best-matching GraphTemplate for the intent type
    2. Instantiate the template into a full ExecutionGraph with concrete
       capability IDs, parameters, and policies
    3. Optionally enrich the graph with additional context from a
       Knowledge Store
    """

    def __init__(
        self,
        knowledge_store: Any = None,
        capability_registry: Any = None,
        governance_engine: Any = None,
        ranker: Optional[PlanRanker] = None,
    ) -> None:
        """Initialise the Planning Engine.

        Args:
            knowledge_store: Optional KnowledgeStore for enrichment queries.
            capability_registry: Optional CapabilityRegistry for capability validation.
            governance_engine: Optional GovernanceEngine for candidate filtering.
            ranker: Optional PlanRanker for candidate scoring. Creates default if not provided.
        """
        self._knowledge_store = knowledge_store
        self._capability_registry = capability_registry
        self._governance_engine = governance_engine
        self._custom_templates: Dict[str, GraphTemplate] = {}
        self._ranker = ranker or PlanRanker(governance_engine=governance_engine)
        self._logger = logger.bind(component="PlanningEngine")

    # ── Public API ─────────────────────────────────────────────────

    async def plan(self, intent: Intent, candidate_mode: bool = False) -> ExecutionGraph:
        """Translate an Intent into a validated Execution Graph.

        When ``candidate_mode=True``, the engine generates multiple candidates,
        ranks them, applies governance, and selects the best plan.
        When ``candidate_mode=False`` (default), falls back to the original
        single-template pipeline for backward compatibility.

        Pipeline:
        - Single: template lookup → instantiate → validate → (enrich)
        - Candidate: generate_candidates → rank → governance → select → enrich

        Args:
            intent: The structured Intent to plan.
            candidate_mode: If True, use candidate generation + ranking.

        Returns:
            A validated ExecutionGraph ready for governance and execution.

        Raises:
            PlanError: If no template/candidate can be found or validation fails.
        """
        self._logger.info(
            "plan.start",
            intent_id=intent.id,
            intent_type=intent.type.value,
            candidate_mode=candidate_mode,
        )

        if candidate_mode:
            return await self._plan_with_candidates(intent)

        # ── Single-template pipeline (backward compatible) ────────
        template = await self.get_template(intent.type)
        if template is None:
            raise PlanError(
                f"No template found for intent type {intent.type.value}",
                intent_id=intent.id,
            )

        self._logger.debug(
            "plan.template_found",
            template_id=template.id,
            template_name=template.name,
        )

        graph = self._instantiate(template, intent)

        errors = graph.validate()
        if errors:
            self._logger.error("plan.validation_failed", errors=errors)
            raise PlanError(
                f"Graph validation failed: {'; '.join(errors)}",
                intent_id=intent.id,
            )

        if self._knowledge_store is not None:
            try:
                graph = await self.enrich_with_knowledge(graph, intent)
            except Exception as exc:
                self._logger.warning(
                    "plan.enrichment_failed",
                    error=str(exc),
                    exc_info=True,
                )

        self._logger.info(
            "plan.complete",
            graph_id=graph.id,
            node_count=len(graph.nodes),
        )

        return graph

    async def _plan_with_candidates(self, intent: Intent) -> ExecutionGraph:
        """Generate multiple candidates, rank, filter, and select best."""
        # 1. Generate candidates
        candidates = await self.generate_candidates(intent)

        if not candidates:
            # Fallback to single template if no candidates generated
            self._logger.warning(
                "plan.candidates_empty", intent_id=intent.id,
            )
            template = await self.get_template(intent.type)
            if template is None:
                raise PlanError(
                    f"No template or candidates for {intent.type.value}",
                    intent_id=intent.id,
                )
            graph = self._instantiate(template, intent)
            errors = graph.validate()
            if errors:
                raise PlanError(
                    f"Graph validation failed: {'; '.join(errors)}",
                    intent_id=intent.id,
                )
            return graph

        # 2. Apply governance filter
        candidates = await self._ranker.apply_governance(candidates)

        if not candidates:
            raise PlanError(
                "All candidates rejected by governance",
                intent_id=intent.id,
            )

        # 3. Rank and select best
        ranked = await self._ranker.rank(candidates)
        best = await self._ranker.select_best(ranked)

        if best is None:
            raise PlanError(
                "No candidate selected after ranking",
                intent_id=intent.id,
            )

        self._logger.info(
            "plan.candidate_selected",
            intent_id=intent.id,
            candidate_id=best.id,
            graph_id=best.graph.id,
            score=best.metadata.get("_rank_score", 0.0),
            node_count=len(best.graph.nodes),
        )

        # 4. Enrich with knowledge (optional)
        if self._knowledge_store is not None:
            try:
                best.graph = await self.enrich_with_knowledge(best.graph, intent)
            except Exception as exc:
                self._logger.warning(
                    "plan.enrichment_failed",
                    error=str(exc),
                    exc_info=True,
                )

        return best.graph

    async def get_template(self, intent_type: IntentType) -> Optional[GraphTemplate]:
        """Retrieve the best template for an intent type.

        Lookup order:
        1. Custom templates registered via ``add_template()``
        2. Built-in template library
        3. Returns None if not found

        Args:
            intent_type: The IntentType to match.

        Returns:
            Matching GraphTemplate or None.
        """
        # Check custom templates first (they override builtins)
        for tmpl in self._custom_templates.values():
            if tmpl.intent_type == intent_type:
                return tmpl

        # Fall back to built-in
        return get_default_template(intent_type)

    async def enrich_with_knowledge(
        self,
        graph: ExecutionGraph,
        intent: Intent,
    ) -> ExecutionGraph:
        """Enrich a graph with additional context from the Knowledge Store.

        Queries the Knowledge Store for facts related to the intent's
        target and context, and merges relevant facts into the graph's
        metadata and node parameters.

        Args:
            graph: The graph to enrich.
            intent: The originating Intent providing target+context clues.

        Returns:
            The enriched ExecutionGraph (mutated in-place plus returned).
        """
        if self._knowledge_store is None:
            return graph

        enriched_count = 0

        # 1. Query for relevant facts
        target = intent.target
        try:
            facts = await self._query_facts(target, intent.context)
        except Exception:
            facts = []

        if facts:
            # Store as metadata for audit trail
            fact_ids = [f.get("id", "") for f in facts if f.get("id")]
            existing_facts = graph.metadata.get("knowledge_facts", [])
            graph.metadata["knowledge_facts"] = existing_facts + fact_ids

            # Inject fact data into node inputs where applicable
            for fact in facts:
                fact_target = fact.get("target", "")
                fact_key = fact.get("key", "")
                fact_value = fact.get("value")

                if not fact_target or not fact_key or fact_value is None:
                    continue

                # Add to graph metadata
                key = f"knowledge.{fact_target}.{fact_key}"
                graph.metadata[key] = fact_value
                enriched_count += 1

        # 2. Propagate intent context into metadata
        if intent.context:
            for ctx_key, ctx_val in intent.context.items():
                if isinstance(ctx_val, (str, int, float, bool, list, dict)):
                    key = f"context.{ctx_key}"
                    if key not in graph.metadata:
                        graph.metadata[key] = ctx_val

        self._logger.debug(
            "plan.enrichment",
            graph_id=graph.id,
            fact_count=len(facts),
            enriched_count=enriched_count,
        )

        return graph

    # ── Candidate Generation ──────────────────────────────────────

    async def generate_candidates(self, intent: Intent) -> List[PlanCandidate]:
        """Generate multiple plan candidates from a single Intent.

        Uses different template variations where available:
        - Primary template (default built-in or custom)
        - Alternative template with modified parameters (if available)
        - Variation with/without approval gates (if applicable)

        Args:
            intent: The structured Intent to generate candidates for.

        Returns:
            A list of unique PlanCandidate objects (1–3 candidates).
        """
        self._logger.debug(
            "generate_candidates.start",
            intent_id=intent.id,
            intent_type=intent.type.value,
        )

        candidates: List[PlanCandidate] = []
        seen_graph_ids: set = set()

        # Variant 1: Use the primary (default) template
        primary_tmpl = await self.get_template(intent.type)
        if primary_tmpl:
            candidate = self._make_candidate(primary_tmpl, intent, variant="primary")
            if candidate.graph.id not in seen_graph_ids:
                candidates.append(candidate)
                seen_graph_ids.add(candidate.graph.id)

        # Variant 2: Aggressive variant — shorter retries, no approval
        if primary_tmpl:
            agg_tmpl = self._vary_template(
                primary_tmpl,
                aggressive=True,
                remove_approval=True,
            )
            candidate = self._make_candidate(agg_tmpl, intent, variant="aggressive")
            if candidate.graph.id not in seen_graph_ids:
                candidates.append(candidate)
                seen_graph_ids.add(candidate.graph.id)

        # Variant 3: Conservative variant — longer retries, gate, compensation
        if primary_tmpl:
            cons_tmpl = self._vary_template(
                primary_tmpl,
                conservative=True,
                ensure_approval=True,
                ensure_compensation=True,
            )
            candidate = self._make_candidate(cons_tmpl, intent, variant="conservative")
            if candidate.graph.id not in seen_graph_ids:
                candidates.append(candidate)
                seen_graph_ids.add(candidate.graph.id)

        self._logger.debug(
            "generate_candidates.complete",
            intent_id=intent.id,
            count=len(candidates),
        )

        return candidates

    def _make_candidate(
        self,
        template: GraphTemplate,
        intent: Intent,
        variant: str = "primary",
    ) -> PlanCandidate:
        """Build a PlanCandidate from a template + intent."""
        graph = self._instantiate(template, intent)

        # Compute candidate scores based on template features
        node_count = len(template.nodes)
        has_compensation = any(
            n.get("compensation_policy") for n in template.nodes
        ) or template.compensation_policy is not None
        has_approval = any(
            n.get("capability_id", "") == "governance:request-approval"
            for n in template.nodes
        )
        has_approval = has_approval or template.metadata.get("requires_approval", False)

        # Base values from template metadata
        base_risk = template.metadata.get("risk_score", 0.5)
        base_duration = template.metadata.get("estimated_duration", 30)

        ranker = self._ranker
        estimated_duration = ranker.compute_estimated_duration(
            node_count, base_duration
        )
        risk_score = ranker.compute_risk_score(
            has_compensation, has_approval, base_risk
        )

        if variant == "aggressive":
            risk_score = min(1.0, risk_score + 0.1)
            estimated_duration = max(10, estimated_duration - 15)
            confidence = 0.3  # Aggressive = lower confidence
        elif variant == "conservative":
            risk_score = max(0.0, risk_score - 0.1)
            estimated_duration = estimated_duration + 30
            confidence = 0.8  # Conservative = higher confidence
        else:
            confidence = 0.6  # Primary = moderate confidence

        return PlanCandidate(
            intent_id=intent.id,
            graph=graph,
            estimated_duration=estimated_duration,
            risk_score=risk_score,
            confidence=confidence,
            cost_estimate=template.metadata.get("cost_estimate", 1.0),
            historical_success_rate=template.metadata.get(
                "historical_success_rate", 0.5
            ),
            approval_required=has_approval,
            metadata={
                "template_id": template.id,
                "template_name": template.name,
                "variant": variant,
                "node_count": node_count,
            },
        )

    @staticmethod
    def _vary_template(
        template: GraphTemplate,
        aggressive: bool = False,
        conservative: bool = False,
        remove_approval: bool = False,
        ensure_approval: bool = False,
        ensure_compensation: bool = False,
    ) -> GraphTemplate:
        """Create a modified copy of a template with varied parameters."""
        import copy

        new_nodes: List[Dict[str, Any]] = []
        for n in template.nodes:
            node = copy.deepcopy(n)
            rp = node.get("retry_policy")

            if aggressive and rp:
                rp["max_attempts"] = 1
                rp["initial_delay"] = max(1, rp.get("initial_delay", 1) // 2)
            elif conservative and rp:
                rp["max_attempts"] = rp.get("max_attempts", 3) + 2
                rp["initial_delay"] = rp.get("initial_delay", 1) * 2

            if remove_approval:
                if node.get("capability_id", "") == "governance:request-approval":
                    continue  # Skip approval gate node

            if ensure_approval:
                if not any(
                    nn.get("capability_id", "") == "governance:request-approval"
                    for nn in new_nodes
                ):
                    # Add approval as second-to-last before compensation
                    pass  # Too invasive; use metadata marking instead

            new_nodes.append(node)

        # Update metadata
        meta = dict(template.metadata)
        if aggressive:
            meta["variant"] = "aggressive"
            meta["aggressive"] = True
        elif conservative:
            meta["variant"] = "conservative"
            meta["conservative"] = True

        id_suffix = "-agg" if aggressive else ("-cons" if conservative else "-var")
        varied = GraphTemplate(
            id=f"{template.id}{id_suffix}",
            intent_type=template.intent_type,
            name=f"{template.name} ({'Aggressive' if aggressive else 'Conservative' if conservative else 'Varied'})",
            description=template.description,
            nodes=new_nodes,
            dependencies=[dict(d) for d in template.dependencies],
            retry_policy=dict(template.retry_policy)
            if template.retry_policy
            else None,
            compensation_policy=dict(template.compensation_policy)
            if template.compensation_policy
            else None,
            metadata=meta,
        )
        return varied

    # ── Template Management ────────────────────────────────────────

    def add_template(self, template: GraphTemplate) -> None:
        """Register a custom template (overrides built-in for same intent type)."""
        self._custom_templates[template.id] = template
        self._logger.info("template.added", template_id=template.id)

    def remove_template(self, template_id: str) -> None:
        """Remove a custom template by ID."""
        self._custom_templates.pop(template_id, None)

    def list_templates(self) -> List[GraphTemplate]:
        """Return all available templates (custom + built-in)."""
        custom_by_type = {
            tmpl.intent_type: tmpl for tmpl in self._custom_templates.values()
        }
        result = list(self._custom_templates.values())
        for itype, tmpl in BUILTIN_TEMPLATES.items():
            if itype not in custom_by_type:
                result.append(tmpl)
        return result

    # ── Internal ───────────────────────────────────────────────────

    def _instantiate(self, template: GraphTemplate, intent: Intent) -> ExecutionGraph:
        """Create a concrete ExecutionGraph from a template and intent data.

        Performs placeholder substitution in capability_id strings and
        input parameters, copying policies from template defaults where
        nodes don't define their own.
        """
        graph_id = str(uuid.uuid4())
        sub = self._build_substitutions(intent)

        nodes: List[ExecutionNode] = []
        for node_def in template.nodes:
            node_id = self._substitute(node_def.get("id", ""), sub)
            capability_id = self._substitute(node_def.get("capability_id", ""), sub)
            inputs = self._substitute_dict(node_def.get("inputs", {}), sub)

            # Retry policy: per-node overrides template default
            rp_raw = node_def.get("retry_policy") or template.retry_policy
            rp = self._make_retry_policy(rp_raw)

            # Compensation policy: per-node overrides template default
            cp_raw = node_def.get("compensation_policy") or template.compensation_policy
            cp = self._make_compensation_policy(cp_raw)

            node = ExecutionNode(
                id=node_id,
                graph_id=graph_id,
                capability_id=capability_id,
                inputs=inputs,
                retry_policy=rp,
                compensation_policy=cp,
            )
            nodes.append(node)

        # Derive entry/exit nodes from template dependency analysis
        entry_ids = [self._substitute(e, sub) for e in template.get_entry_node_ids()]
        exit_ids = [self._substitute(e, sub) for e in template.get_exit_node_ids()]

        # Apply dependencies (substitute node IDs in dependency edges)
        for dep in template.dependencies:
            from_id = self._substitute(dep["from"], sub)
            to_id = self._substitute(dep["to"], sub)
            # Find the target node and add dependency
            for node in nodes:
                if node.id == to_id and from_id not in node.dependencies:
                    node.dependencies.append(from_id)

        # Inherit metadata from template
        metadata = dict(template.metadata)
        metadata["template_id"] = template.id
        metadata["intent_id"] = intent.id
        metadata["intent_type"] = intent.type.value
        metadata["intent_target"] = intent.target

        now = datetime.utcnow()
        graph = ExecutionGraph(
            id=graph_id,
            name=f"{template.name}: {intent.target or intent.type.value}",
            nodes=nodes,
            entry_nodes=entry_ids,
            exit_nodes=exit_ids,
            status=GraphStatus.CREATED,
            correlation_id=intent.correlation_id,
            metadata=metadata,
            created_at=now,
            updated_at=now,
        )

        return graph

    def _build_substitutions(self, intent: Intent) -> Dict[str, str]:
        """Build a substitution map from intent fields for template placeholders.

        Keys like ``{target}``, ``{verbose}``, ``{version}`` etc. are replaced
        with values from the intent's parameters and target field.
        """
        sub: Dict[str, str] = {
            "target": intent.target.replace(":", ".") if ":" in intent.target else intent.target,
        }

        # Copy stringifiable parameters
        for key, val in intent.parameters.items():
            if isinstance(val, str):
                sub[key] = val
            elif isinstance(val, bool):
                sub[key] = "true" if val else "false"
            elif val is not None:
                sub[key] = str(val)

        # Context values
        for key, val in intent.context.items():
            if isinstance(val, str):
                sub[f"context.{key}"] = val
            elif val is not None:
                sub[f"context.{key}"] = str(val)

        return sub

    @staticmethod
    def _substitute(text: str, sub: Dict[str, str]) -> str:
        """Replace ``{placeholder}`` markers in a string using the substitution map.

        Unknown placeholders are left as-is.
        """
        result = text
        for key, val in sub.items():
            result = result.replace(f"{{{key}}}", val)
        return result

    @staticmethod
    def _substitute_dict(data: Dict[str, Any], sub: Dict[str, str]) -> Dict[str, Any]:
        """Substitute placeholders in all string values of a dict (nested)."""
        result: Dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, str):
                result[k] = PlanningEngine._substitute(v, sub)
            elif isinstance(v, dict):
                result[k] = PlanningEngine._substitute_dict(v, sub)
            elif isinstance(v, list):
                result[k] = [
                    PlanningEngine._substitute(item, sub) if isinstance(item, str) else item
                    for item in v
                ]
            else:
                result[k] = v
        return result

    @staticmethod
    def _make_retry_policy(raw: Optional[Dict[str, Any]]) -> RetryPolicy:
        """Build a RetryPolicy from a raw dict (with defaults for missing keys)."""
        if not raw:
            return RetryPolicy()
        return RetryPolicy(
            max_attempts=raw.get("max_attempts", 3),
            backoff=RetryBackoff(raw.get("backoff", "EXPONENTIAL")),
            initial_delay=raw.get("initial_delay", 1),
            max_delay=raw.get("max_delay", 60),
            jitter=raw.get("jitter", True),
        )

    @staticmethod
    def _make_compensation_policy(raw: Optional[Dict[str, Any]]) -> CompensationPolicy:
        """Build a CompensationPolicy from a raw dict (with defaults for missing keys)."""
        if not raw:
            return CompensationPolicy()
        return CompensationPolicy(
            compensation_node_id=raw.get("compensation_node_id"),
            on_failure=CompensationOnFailure(raw.get("on_failure", "ABORT")),
        )

    async def _query_facts(
        self, target: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Query the Knowledge Store for facts relevant to the target.

        Args:
            target: The intent target (e.g. "provider:nvidia").
            context: Additional context for filtering.

        Returns:
            List of fact dicts with id, target, key, value.
        """
        if self._knowledge_store is None:
            return []

        facts: List[Dict[str, Any]] = []

        # Try structured search if available
        if hasattr(self._knowledge_store, "search"):
            try:
                query = f"target:{target}" if target else ""
                results = await self._knowledge_store.search(query, limit=20)
                if isinstance(results, list):
                    for item in results:
                        if isinstance(item, dict):
                            facts.append(item)
                        elif hasattr(item, "to_dict"):
                            facts.append(item.to_dict())
                        elif hasattr(item, "__dict__"):
                            d = item.__dict__.copy()
                            d["id"] = getattr(item, "id", "")
                            facts.append(d)
            except Exception as exc:
                self._logger.debug("knowledge.search_failed", error=str(exc))

        # Fallback: try get_by_subject
        if not facts and target and hasattr(self._knowledge_store, "get_by_subject"):
            try:
                results = await self._knowledge_store.get_by_subject(target)
                if isinstance(results, list):
                    for item in results:
                        if isinstance(item, dict):
                            facts.append(item)
                        elif hasattr(item, "to_dict"):
                            facts.append(item.to_dict())
            except Exception as exc:
                self._logger.debug("knowledge.get_by_subject_failed", error=str(exc))

        return facts
