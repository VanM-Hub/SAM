"""Unit tests for metadata validation (Tugas 9.3)."""

import pytest
from unittest.mock import AsyncMock, patch

from sam.validation import (
    validate_capability_metadata,
    validate_and_build_descriptor,
    ValidationError,
    CapabilityDescriptor,
    VALID_RISK_LEVELS,
)


class TestValidateCapabilityMetadata:
    """Tests for validate_capability_metadata function."""

    def test_happy_path_minimal_valid_metadata(self):
        """Test that minimal valid metadata passes validation."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test capability",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert errors == []

    def test_happy_path_full_metadata(self):
        """Test that full valid metadata passes validation."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "2.3.4",
            "risk_level": "High",
            "description": "A test capability with all fields",
            "implementation": "sam.capabilities.test.TestCapability",
            "permissions": ["read", "write"],
            "dependencies": ["other.capability"],
            "tags": ["test", "observation"],
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert errors == []

    def test_missing_capability_id_fails(self):
        """Test that missing capability_id fails validation."""
        metadata = {
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test capability",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("capability_id" in e for e in errors)

    def test_empty_capability_id_fails(self):
        """Test that empty capability_id fails validation."""
        metadata = {
            "capability_id": "",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test capability",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("capability_id" in e for e in errors)

    def test_bad_semver_fails(self):
        """Test that invalid SemVer version fails validation."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "invalid",
            "risk_level": "Low",
            "description": "Test capability",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("SemVer" in e or "version" in e for e in errors)

    def test_partial_semver_fails(self):
        """Test that partial SemVer (1.0) fails validation."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0",
            "risk_level": "Low",
            "description": "Test capability",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("SemVer" in e or "version" in e for e in errors)

    def test_valid_semver_passes(self):
        """Test that valid SemVer versions pass."""
        for version in ["1.0.0", "2.3.4", "10.20.30", "1.0.0-alpha", "2.0.0-beta.1"]:
            metadata = {
                "capability_id": "test.capability",
                "capability_type": "observation.test",
                "version": version,
                "risk_level": "Low",
                "description": "Test capability",
            }
            errors = validate_capability_metadata(metadata, "test.md", set())
            assert not any("SemVer" in e or "version" in e for e in errors), f"Failed for version {version}: {errors}"

    def test_invalid_risk_level_fails(self):
        """Test that invalid risk_level fails validation."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Unknown",
            "description": "Test capability",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("risk_level" in e for e in errors)

    def test_all_valid_risk_levels_pass(self):
        """Test that all valid risk levels pass."""
        for level in VALID_RISK_LEVELS:
            metadata = {
                "capability_id": "test.capability",
                "capability_type": "observation.test",
                "version": "1.0.0",
                "risk_level": level,
                "description": "Test capability",
            }
            errors = validate_capability_metadata(metadata, "test.md", set())
            assert not any("risk_level" in e for e in errors), f"Failed for risk_level {level}: {errors}"

    def test_missing_capability_type_fails(self):
        """Test that missing capability_type fails validation."""
        metadata = {
            "capability_id": "test.capability",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test capability",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("capability_type" in e for e in errors)

    def test_empty_capability_type_fails(self):
        """Test that empty capability_type fails validation."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test capability",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("capability_type" in e for e in errors)

    def test_missing_description_fails(self):
        """Test that missing description fails validation."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("description" in e for e in errors)

    def test_empty_description_fails(self):
        """Test that empty description fails validation."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("description" in e for e in errors)

    def test_whitespace_description_fails(self):
        """Test that whitespace-only description fails validation."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "   ",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("description" in e for e in errors)

    def test_permissions_as_list_passes(self):
        """Test that permissions as list passes."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "permissions": ["read", "write"],
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert not any("permissions" in e for e in errors)

    def test_permissions_as_comma_string_passes(self):
        """Test that permissions as comma-separated string passes."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "permissions": "read, write, execute",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert not any("permissions" in e for e in errors)

    def test_permissions_as_invalid_type_fails(self):
        """Test that permissions as non-list/string fails."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "permissions": 123,
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert any("permissions" in e for e in errors)

    def test_dependencies_as_list_passes(self):
        """Test that dependencies as list passes."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "dependencies": ["dep1", "dep2"],
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert not any("dependencies" in e for e in errors)

    def test_dependencies_as_comma_string_passes(self):
        """Test that dependencies as comma-separated string passes."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "dependencies": "dep1, dep2",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert not any("dependencies" in e for e in errors)

    def test_tags_as_list_passes(self):
        """Test that tags as list passes."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "tags": ["tag1", "tag2"],
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert not any("tags" in e for e in errors)

    def test_tags_as_comma_string_passes(self):
        """Test that tags as comma-separated string passes."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "tags": "tag1, tag2",
        }
        errors = validate_capability_metadata(metadata, "test.md", set())
        assert not any("tags" in e for e in errors)

    def test_duplicate_capability_id_fails(self):
        """Test that duplicate capability_id fails validation."""
        existing = {"existing.capability"}
        metadata = {
            "capability_id": "existing.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test capability",
        }
        errors = validate_capability_metadata(metadata, "test.md", existing)
        assert any("duplicate" in e.lower() for e in errors)

    def test_source_document_warning_not_error(self):
        """Test that missing source_document doesn't cause validation error (warning only)."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test capability",
        }
        # source_document that doesn't exist - should NOT add error
        errors = validate_capability_metadata(metadata, "nonexistent/path/test.md", set())
        # Should NOT have errors about source_document
        assert not any("source_document" in e for e in errors)
        # Should have no errors (the missing source_doc is a warning, not error)
        assert errors == []


class TestValidateAndBuildDescriptor:
    """Tests for validate_and_build_descriptor function."""

    @pytest.mark.asyncio
    async def test_happy_path_builds_descriptor(self):
        """Test that valid metadata builds a CapabilityDescriptor."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "A test capability",
        }
        descriptor = await validate_and_build_descriptor(metadata, "test.md", set())
        
        assert isinstance(descriptor, CapabilityDescriptor)
        assert descriptor.id == "test.capability"
        assert descriptor.capability_type == "observation.test"
        assert descriptor.version == "1.0.0"
        assert descriptor.risk_level == "Low"
        assert descriptor.description == "A test capability"
        assert descriptor.source_document == "test.md"
        assert descriptor.enabled is True

    @pytest.mark.asyncio
    async def test_missing_capability_id_raises_validation_error(self):
        """Test that missing capability_id raises ValidationError."""
        metadata = {
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
        }
        with pytest.raises(ValidationError) as exc_info:
            await validate_and_build_descriptor(metadata, "test.md", set())
        assert exc_info.value.capability_id == ""
        assert any("capability_id" in e for e in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_bad_semver_raises_validation_error(self):
        """Test that invalid SemVer raises ValidationError with errors."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "not-semver",
            "risk_level": "Low",
            "description": "Test",
        }
        with pytest.raises(ValidationError) as exc_info:
            await validate_and_build_descriptor(metadata, "test.md", set())
        assert exc_info.value.capability_id == "test.capability"
        assert any("SemVer" in e or "version" in e for e in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_invalid_risk_level_raises_validation_error(self):
        """Test that invalid risk_level raises ValidationError."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Invalid",
            "description": "Test",
        }
        with pytest.raises(ValidationError) as exc_info:
            await validate_and_build_descriptor(metadata, "test.md", set())
        assert exc_info.value.capability_id == "test.capability"
        assert any("risk_level" in e for e in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_duplicate_id_raises_validation_error(self):
        """Test that duplicate capability_id raises ValidationError."""
        existing = {"existing.capability"}
        metadata = {
            "capability_id": "existing.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
        }
        with pytest.raises(ValidationError) as exc_info:
            await validate_and_build_descriptor(metadata, "test.md", existing)
        assert exc_info.value.capability_id == "existing.capability"
        assert any("duplicate" in e.lower() for e in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_implementation_import_check(self):
        """Test that implementation import is validated."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "implementation": "nonexistent.module.NonExistentClass",
        }
        with pytest.raises(ValidationError) as exc_info:
            await validate_and_build_descriptor(metadata, "test.md", set())
        assert any("import" in e.lower() or "module" in e.lower() for e in exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_permissions_parsed_correctly(self):
        """Test that permissions are parsed from comma-separated string."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "permissions": "read, write, execute",
        }
        descriptor = await validate_and_build_descriptor(metadata, "test.md", set())
        assert descriptor.permissions == ["read", "write", "execute"]

    @pytest.mark.asyncio
    async def test_dependencies_parsed_correctly(self):
        """Test that dependencies are parsed from comma-separated string."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "dependencies": "dep1, dep2",
        }
        descriptor = await validate_and_build_descriptor(metadata, "test.md", set())
        assert descriptor.dependencies == ["dep1", "dep2"]

    @pytest.mark.asyncio
    async def test_tags_parsed_correctly(self):
        """Test that tags are parsed from comma-separated string."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
            "tags": "tag1, tag2",
        }
        descriptor = await validate_and_build_descriptor(metadata, "test.md", set())
        assert descriptor.tags == ["tag1", "tag2"]

    @pytest.mark.asyncio
    async def test_empty_lists_for_optional_fields(self):
        """Test that optional fields default to empty lists when not provided."""
        metadata = {
            "capability_id": "test.capability",
            "capability_type": "observation.test",
            "version": "1.0.0",
            "risk_level": "Low",
            "description": "Test",
        }
        descriptor = await validate_and_build_descriptor(metadata, "test.md", set())
        assert descriptor.permissions == []
        assert descriptor.dependencies == []
        assert descriptor.tags == []


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_stores_info(self):
        """Test that ValidationError stores capability_id and errors."""
        error = ValidationError(capability_id="test.id", errors=["error1", "error2"])
        assert error.capability_id == "test.id"
        assert error.errors == ["error1", "error2"]

    def test_validation_error_str_representation(self):
        """Test ValidationError string representation."""
        error = ValidationError(capability_id="test.id", errors=["error1", "error2"])
        s = str(error)
        assert "test.id" in s
        assert "error1" in s
        assert "error2" in s