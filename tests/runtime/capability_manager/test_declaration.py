"""Tests for CapabilityDeclaration model + DeclarationValidator.

Verifies: declaration creation, validation, forbidden patterns.

Authority: I2-002 §6.1
"""

import pytest

from sam.runtime.capability_manager import CapabilityDeclaration
from sam.runtime.capability_manager.validation.declaration_validator import (
    DeclarationValidator,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    InvalidDeclaration,
)


class TestCapabilityDeclaration:
    """Tests for CapabilityDeclaration model."""

    def test_create_with_required_fields(self) -> None:
        """Declaration can be created with identity, name, version."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="Memory Lookup",
            version="1.0.0",
        )
        assert decl.identity == "memory.lookup"
        assert decl.name == "Memory Lookup"
        assert decl.version == "1.0.0"

    def test_create_with_all_fields(self) -> None:
        """Declaration accepts all optional fields."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="Memory Lookup",
            version="1.0.0",
            owner_citizen="citizen-001",
            description="Look up items",
            inputs=["query"],
            outputs=["results"],
            constraints=["max=100"],
            compatibility=["1.0.x"],
        )
        assert decl.owner_citizen == "citizen-001"
        assert decl.inputs == ["query"]
        assert decl.compatibility == ["1.0.x"]

    def test_validate_required_valid(self) -> None:
        """validate_required returns True for complete declaration."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="Memory Lookup",
            version="1.0.0",
        )
        assert decl.validate_required() is True

    def test_validate_required_empty_identity(self) -> None:
        """validate_required returns False for empty identity."""
        decl = CapabilityDeclaration(
            identity="",
            name="Memory Lookup",
            version="1.0.0",
        )
        assert decl.validate_required() is False

    def test_validate_required_empty_name(self) -> None:
        """validate_required returns False for empty name."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="",
            version="1.0.0",
        )
        assert decl.validate_required() is False

    def test_validate_required_empty_version(self) -> None:
        """validate_required returns False for empty version."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="Memory Lookup",
            version="",
        )
        assert decl.validate_required() is False


class TestDeclarationValidator:
    """Tests for DeclarationValidator."""

    def setup_method(self) -> None:
        self.validator = DeclarationValidator()

    def test_valid_declaration_passes(self) -> None:
        """A valid declaration passes validation."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="Memory Lookup",
            version="1.0.0",
        )
        assert self.validator.validate(decl) is True

    def test_empty_identity_raises(self) -> None:
        """Empty identity raises InvalidDeclaration."""
        decl = CapabilityDeclaration(
            identity="",
            name="Memory Lookup",
            version="1.0.0",
        )
        with pytest.raises(InvalidDeclaration, match="identity"):
            self.validator.validate(decl)

    def test_empty_name_raises(self) -> None:
        """Empty name raises InvalidDeclaration."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="",
            version="1.0.0",
        )
        with pytest.raises(InvalidDeclaration, match="name"):
            self.validator.validate(decl)

    def test_empty_version_raises(self) -> None:
        """Empty version raises InvalidDeclaration."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="Memory Lookup",
            version="",
        )
        with pytest.raises(InvalidDeclaration, match="version"):
            self.validator.validate(decl)

    def test_identity_contains_implementation_name(self) -> None:
        """Identity with implementation name raises InvalidDeclaration."""
        decl = CapabilityDeclaration(
            identity="openai.chat",
            name="Chat",
            version="1.0.0",
        )
        with pytest.raises(InvalidDeclaration, match="openai"):
            self.validator.validate(decl)

    def test_identity_contains_gpt(self) -> None:
        """Identity with 'gpt' raises InvalidDeclaration."""
        decl = CapabilityDeclaration(
            identity="provider.gpt4",
            name="GPT4 Provider",
            version="1.0.0",
        )
        with pytest.raises(InvalidDeclaration, match="gpt"):
            self.validator.validate(decl)

    def test_invalid_version_format(self) -> None:
        """Non-semver version raises InvalidDeclaration."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="Memory Lookup",
            version="v1.0",
        )
        with pytest.raises(InvalidDeclaration, match="(?i)version"):
            self.validator.validate(decl)

    def test_valid_version_formats(self) -> None:
        """Various valid semver formats pass."""
        for version in ["0.0.1", "1.0.0", "10.20.30", "99.99.99"]:
            decl = CapabilityDeclaration(
                identity="memory.lookup",
                name="Memory Lookup",
                version=version,
            )
            assert self.validator.validate(decl) is True
