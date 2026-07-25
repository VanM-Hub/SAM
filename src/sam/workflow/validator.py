"""Workflow validator for checking workflow definitions."""

from typing import List, Set

from sam.runtime.registry import CapabilityRegistry

from .models import WorkflowDefinition, WorkflowStep


class WorkflowValidator:
    """Validates workflow definitions against registry and structural rules."""

    def __init__(self) -> None:
        pass

    async def validate(self, definition: WorkflowDefinition, registry: CapabilityRegistry) -> List[str]:
        """Validate a workflow definition.

        Args:
            definition: The workflow definition to validate
            registry: Capability registry to check capability availability

        Returns:
            List of error messages (empty if valid)
        """
        errors: List[str] = []

        # 1. Check unique step IDs
        errors.extend(self._check_unique_step_ids(definition))

        # 2. Check all capabilities exist in registry
        errors.extend(await self._check_capabilities_exist(definition, registry))

        # 3. Check transitions reference valid step IDs
        errors.extend(self._check_transitions_valid(definition))

        # 4. Check no unreachable steps
        errors.extend(self._check_no_unreachable_steps(definition))

        # 5. Check no cycles (using DFS)
        errors.extend(self._check_no_cycles(definition))

        return errors

    def _check_unique_step_ids(self, definition: WorkflowDefinition) -> List[str]:
        """Check that all step IDs are unique."""
        errors: List[str] = []
        seen: Set[str] = set()
        for step in definition.steps:
            if step.id in seen:
                errors.append(f"Duplicate step ID: {step.id}")
            seen.add(step.id)
        return errors

    async def _check_capabilities_exist(self, definition: WorkflowDefinition, registry: CapabilityRegistry) -> List[str]:
        """Check that all referenced capabilities are registered."""
        errors: List[str] = []
        for step in definition.steps:
            descriptor = await registry.get_descriptor(step.capability)
            if descriptor is None:
                errors.append(f"Capability not registered: {step.capability} (referenced by step '{step.id}')")
        return errors

    def _check_transitions_valid(self, definition: WorkflowDefinition) -> List[str]:
        """Check that all transitions reference valid step IDs."""
        errors: List[str] = []
        step_ids = {step.id for step in definition.steps}

        for step in definition.steps:
            trans = step.transition
            for field_name, target in [
                ("on_success", trans.on_success),
                ("on_failure", trans.on_failure),
                ("on_timeout", trans.on_timeout),
            ]:
                if target is not None and target not in step_ids:
                    errors.append(f"Step '{step.id}' transition '{field_name}' references unknown step: {target}")
        return errors

    def _check_no_unreachable_steps(self, definition: WorkflowDefinition) -> List[str]:
        """Check that all steps are reachable from the first step."""
        errors: List[str] = []
        if not definition.steps:
            return errors

        step_ids = {step.id for step in definition.steps}
        start_id = definition.steps[0].id

        # Build adjacency list
        graph = {sid: [] for sid in step_ids}
        for step in definition.steps:
            for target in [step.transition.on_success, step.transition.on_failure, step.transition.on_timeout]:
                if target:
                    graph[step.id].append(target)

        # BFS from start
        reachable: Set[str] = set()
        queue = [start_id]
        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(graph.get(current, []))

        unreachable = step_ids - reachable
        for step_id in unreachable:
            errors.append(f"Unreachable step: {step_id}")

        return errors

    def _check_no_cycles(self, definition: WorkflowDefinition) -> List[str]:
        """Check for cycles in the workflow graph."""
        errors: List[str] = []
        if not definition.steps:
            return errors

        step_ids = {step.id for step in definition.steps}

        # Build adjacency list
        graph = {sid: [] for sid in step_ids}
        for step in definition.steps:
            for target in [step.transition.on_success, step.transition.on_failure, step.transition.on_timeout]:
                if target:
                    graph[step.id].append(target)

        # DFS cycle detection
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Cycle found
                    cycle_start = path.index(neighbor)
                    cycle = " -> ".join(path[cycle_start:] + [neighbor])
                    errors.append(f"Cycle detected: {cycle}")
                    return True

            rec_stack.remove(node)
            return False

        for step_id in step_ids:
            if step_id not in visited:
                dfs(step_id, [])

        return errors