"""Unit tests for CorrelationContext model and correlation propagation (Tugas 9.4)."""

import pytest
from uuid import UUID

from sam.models.correlation import (
    CorrelationContext,
    generate_correlation_id,
    generate_workflow_id,
    generate_execution_id,
)


class TestCorrelationContext:
    """Tests for CorrelationContext model."""

    def test_new_creates_unique_correlation_id(self):
        """Test that new() creates a unique correlation_id."""
        ctx1 = CorrelationContext.new()
        ctx2 = CorrelationContext.new()
        assert ctx1.correlation_id != ctx2.correlation_id
        # Verify it's a valid UUID
        UUID(ctx1.correlation_id)
        UUID(ctx2.correlation_id)

    def test_new_with_workflow_id(self):
        """Test that new() accepts workflow_id."""
        ctx = CorrelationContext.new(workflow_id="wf-123")
        assert ctx.workflow_id == "wf-123"
        assert ctx.correlation_id is not None

    def test_new_with_execution_id(self):
        """Test that new() accepts execution_id."""
        ctx = CorrelationContext.new(execution_id="exec-456")
        assert ctx.execution_id == "exec-456"
        assert ctx.correlation_id is not None

    def test_new_with_parent_id(self):
        """Test that new() accepts parent_id."""
        ctx = CorrelationContext.new(parent_id="parent-789")
        assert ctx.parent_id == "parent-789"
        assert ctx.correlation_id is not None

    def test_new_with_metadata(self):
        """Test that new() accepts metadata."""
        ctx = CorrelationContext.new(metadata={"key": "value", "env": "test"})
        assert ctx.metadata == {"key": "value", "env": "test"}

    def test_child_of_inherits_correlation_id(self):
        """Test that child_of inherits correlation_id from parent."""
        parent = CorrelationContext.new(workflow_id="wf-1")
        child = CorrelationContext.child_of(parent)
        
        assert child.correlation_id == parent.correlation_id

    def test_child_of_can_override_workflow_id(self):
        """Test that child_of() can override workflow_id."""
        parent = CorrelationContext.new(workflow_id="wf-parent")
        child = CorrelationContext.child_of(parent, workflow_id="wf-child")
        
        assert child.workflow_id == "wf-child"
        assert child.correlation_id == parent.correlation_id

    def test_child_of_can_override_execution_id(self):
        """Test that child_of() can override execution_id."""
        parent = CorrelationContext.new(execution_id="exec-parent")
        child = CorrelationContext.child_of(parent, execution_id="exec-child")
        
        assert child.execution_id == "exec-child"
        assert child.correlation_id == parent.correlation_id

    def test_child_of_sets_parent_id(self):
        """Test that child_of() sets parent_id to parent's execution_id or workflow_id."""
        parent = CorrelationContext.new(workflow_id="wf-parent", execution_id="exec-parent")
        child = CorrelationContext.child_of(parent)
        
        assert child.parent_id == "exec-parent"  # execution_id takes precedence

    def test_child_of_sets_parent_id_from_workflow_when_no_execution(self):
        """Test that child_of() sets parent_id to workflow_id when no execution_id."""
        parent = CorrelationContext.new(workflow_id="wf-parent")
        child = CorrelationContext.child_of(parent)
        
        assert child.parent_id == "wf-parent"

    def test_child_of_merges_metadata(self):
        """Test that child_of() merges parent and child metadata."""
        parent = CorrelationContext.new(metadata={"parent_key": "parent_value"})
        child = CorrelationContext.child_of(parent, metadata={"child_key": "child_value"})
        
        assert child.metadata == {"parent_key": "parent_value", "child_key": "child_value"}

    def test_child_of_child_metadata_overrides_parent(self):
        """Test that child metadata overrides parent metadata for same key."""
        parent = CorrelationContext.new(metadata={"key": "parent_value"})
        child = CorrelationContext.child_of(parent, metadata={"key": "child_value"})
        
        assert child.metadata["key"] == "child_value"

    def test_with_workflow_returns_new_context(self):
        """Test that with_workflow() returns a new context with updated workflow_id."""
        original = CorrelationContext.new(workflow_id="original")
        updated = original.with_workflow("new-workflow")
        
        assert updated.workflow_id == "new-workflow"
        assert updated.correlation_id == original.correlation_id
        assert updated is not original  # Should be a new object

    def test_with_execution_returns_new_context(self):
        """Test that with_execution() returns a new context with updated execution_id."""
        original = CorrelationContext.new(execution_id="original")
        updated = original.with_execution("new-execution")
        
        assert updated.execution_id == "new-execution"
        assert updated.correlation_id == original.correlation_id
        assert updated is not original

    def test_to_log_context_returns_dict(self):
        """Test that to_log_context returns dict with all fields."""
        ctx = CorrelationContext.new(
            workflow_id="test-workflow",
            execution_id="test-execution",
            parent_id="test-parent",
        )
        log_ctx = ctx.to_log_context()
        
        assert log_ctx == {
            "correlation_id": ctx.correlation_id,
            "workflow_id": "test-workflow",
            "execution_id": "test-execution",
            "parent_id": "test-parent",
        }

    def test_to_log_context_with_none_values(self):
        """Test that to_log_context() includes None values."""
        ctx = CorrelationContext.new()
        log_ctx = ctx.to_log_context()
        
        assert "correlation_id" in log_ctx
        assert log_ctx["correlation_id"] == ctx.correlation_id
        assert "workflow_id" in log_ctx
        assert log_ctx["workflow_id"] is None


class TestCorrelationIdGeneration:
    """Tests for correlation ID generation functions."""

    def test_generate_correlation_id_returns_uuid(self):
        """Test that generate_correlation_id returns a valid UUID string."""
        cid = generate_correlation_id()
        assert isinstance(cid, str)
        UUID(cid)  # Should not raise

    def test_generate_correlation_id_unique(self):
        """Test that generate_correlation_id produces unique IDs."""
        ids = {generate_correlation_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_workflow_id_returns_uuid(self):
        """Test that generate_workflow_id returns a valid UUID string."""
        wid = generate_workflow_id()
        assert isinstance(wid, str)
        UUID(wid)

    def test_generate_execution_id_returns_uuid(self):
        """Test that generate_execution_id returns a valid UUID string."""
        eid = generate_execution_id()
        assert isinstance(eid, str)
        UUID(eid)


class TestCorrelationContextImmutability:
    """Tests that CorrelationContext is immutable (Pydantic BaseModel)."""

    def test_correlation_id_accessible_after_creation(self):
        """Test that correlation_id is accessible after creation."""
        ctx = CorrelationContext.new()
        assert ctx.correlation_id is not None
        assert len(ctx.correlation_id) > 0

    def test_model_copy_creates_new_instance(self):
        """Test that model_copy creates a new instance."""
        ctx = CorrelationContext.new(workflow_id="wf-1")
        new_ctx = ctx.model_copy(update={"workflow_id": "wf-2"})
        
        assert new_ctx.workflow_id == "wf-2"
        assert ctx.workflow_id == "wf-1"
        assert new_ctx.correlation_id == ctx.correlation_id
        assert new_ctx is not ctx


class TestCorrelationContextHierarchy:
    """Tests for correlation context hierarchy scenarios."""

    def test_workflow_with_multiple_executions(self):
        """Test a workflow with multiple capability executions sharing correlation_id."""
        # Create workflow context
        workflow_ctx = CorrelationContext.new(
            workflow_id="workflow-123",
            metadata={"source": "cli", "user": "test"}
        )
        
        # Create child contexts for each execution
        exec1 = CorrelationContext.child_of(workflow_ctx, execution_id="exec-1")
        exec2 = CorrelationContext.child_of(workflow_ctx, execution_id="exec-2")
        exec3 = CorrelationContext.child_of(workflow_ctx, execution_id="exec-3")
        
        # All should share the same correlation_id
        assert exec1.correlation_id == exec2.correlation_id == exec3.correlation_id
        assert exec1.correlation_id == workflow_ctx.correlation_id
        
        # Each should have unique execution_id
        assert exec1.execution_id == "exec-1"
        assert exec2.execution_id == "exec-2"
        assert exec3.execution_id == "exec-3"
        
        # Each should have parent_id pointing to workflow
        assert exec1.parent_id == "workflow-123"
        assert exec2.parent_id == "workflow-123"
        assert exec3.parent_id == "workflow-123"

    def test_nested_workflow_hierarchy(self):
        """Test nested workflow (workflow calling another workflow)."""
        # Root workflow
        root = CorrelationContext.new(
            workflow_id="root-workflow",
            metadata={"depth": 0}
        )
        
        # Child workflow
        child_wf = CorrelationContext.child_of(
            root,
            workflow_id="child-workflow",
            metadata={"depth": 1}
        )
        
        # Execution in child workflow
        exec_in_child = CorrelationContext.child_of(
            child_wf,
            execution_id="exec-in-child"
        )
        
        # All share the same correlation_id
        assert root.correlation_id == child_wf.correlation_id == exec_in_child.correlation_id
        
        # Parent chain: exec -> child_wf -> root
        assert exec_in_child.parent_id == "child-workflow"
        assert child_wf.parent_id == "root-workflow"
        
        # Metadata merged
        assert exec_in_child.metadata["depth"] == 1


class TestCorrelationContextSerialization:
    """Tests for CorrelationContext serialization/deserialization."""

    def test_model_dump_includes_all_fields(self):
        """Test that model_dump includes all fields."""
        ctx = CorrelationContext.new(
            workflow_id="wf-1",
            execution_id="exec-1",
            parent_id="parent-1",
            metadata={"custom": "value"}
        )
        data = ctx.model_dump()
        
        assert data["correlation_id"] == ctx.correlation_id
        assert data["workflow_id"] == "wf-1"
        assert data["execution_id"] == "exec-1"
        assert data["parent_id"] == "parent-1"
        assert data["metadata"] == {"custom": "value"}

    def test_model_validate_from_dict(self):
        """Test that model can be recreated from dict."""
        original = CorrelationContext.new(
            workflow_id="wf-1",
            execution_id="exec-1",
        )
        data = original.model_dump()
        recreated = CorrelationContext.model_validate(data)
        
        assert recreated.correlation_id == original.correlation_id
        assert recreated.workflow_id == original.workflow_id
        assert recreated.execution_id == original.execution_id