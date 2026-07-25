"""
Version Constraint Parsing and Validation for SAM Plugin Framework.

Provides utilities to parse and evaluate semantic version constraints
following SemVer specification with support for:
- Comparison operators: >=, <=, >, <, ==, !=
- Compatible release: ~= (tilde)
- Caret range: ^ (caret)
"""

import re
from typing import Dict, List, Tuple, Optional, Union
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet, InvalidSpecifier


# Supported operators
OPERATORS = [">=", "<=", ">", "<", "==", "!=", "~=", "^"]


class VersionConstraintError(ValueError):
    """Raised when version constraint parsing or evaluation fails."""
    pass


def parse_version_constraint(constraint: str) -> Dict[str, Union[str, List[str]]]:
    """
    Parse a version constraint string into a structured representation.

    Args:
        constraint: Version constraint string (e.g., ">=1.0.0", "~=2.0.0", "^1.2.3")

    Returns:
        Dictionary with parsed constraint information:
        - "operator": The operator used (>=, <=, >, <, ==, !=, ~=, ^)
        - "version": The version string
        - "specifier": The full specifier string for SpecifierSet

    Raises:
        VersionConstraintError: If constraint format is invalid

    Examples:
        >>> parse_version_constraint(">=1.0.0")
        {'operator': '>=', 'version': '1.0.0', 'specifier': '>=1.0.0'}

        >>> parse_version_constraint("^1.2.3")
        {'operator': '^', 'version': '1.2.3', 'specifier': '>=1.2.3,<2.0.0'}
    """
    if not constraint or not constraint.strip():
        raise VersionConstraintError("Empty constraint string")

    constraint = constraint.strip()

    # Find operator
    operator = None
    version_part = None

    for op in OPERATORS:
        if constraint.startswith(op):
            operator = op
            version_part = constraint[len(op):].strip()
            break

    if operator is None:
        # Assume exact match if no operator
        operator = "=="
        version_part = constraint

    if not version_part:
        raise VersionConstraintError(f"Missing version in constraint: {constraint}")

    # Validate version format
    try:
        Version(version_part)
    except InvalidVersion as e:
        raise VersionConstraintError(f"Invalid version '{version_part}': {e}")

    # Convert to specifier string for packaging.specifiers
    if operator == "^":
        # Caret range: ^1.2.3 => >=1.2.3,<2.0.0 (allows patch and minor updates)
        try:
            v = Version(version_part)
            major = v.major
            minor = v.minor
            patch = v.micro
            if major == 0 and minor == 0:
                # 0.0.x - only patch changes allowed
                specifier = f">={version_part},<0.0.{patch + 1}"
            elif major == 0:
                # 0.x.y - only minor and patch changes allowed
                specifier = f">={version_part},<0.{minor + 1}.0"
            else:
                # x.y.z - minor and patch changes allowed
                specifier = f">={version_part},<{major + 1}.0.0"
        except InvalidVersion:
            raise VersionConstraintError(f"Invalid version for caret: {version_part}")
    elif operator == "~=":
        # Compatible release: ~=1.2.3 => >=1.2.3,==1.2.*
        # For SemVer, this means >=1.2.3,<1.3.0
        try:
            v = Version(version_part)
            major = v.major
            minor = v.minor
            if major == 0:
                specifier = f">={version_part},<0.{minor + 1}.0"
            else:
                specifier = f">={version_part},<{major}.{minor + 1}.0"
        except InvalidVersion:
            raise VersionConstraintError(f"Invalid version for tilde: {version_part}")
    else:
        # Standard operators
        specifier = f"{operator}{version_part}"

    return {
        "operator": operator,
        "version": version_part,
        "specifier": specifier
    }


def satisfies(version: str, constraint: str) -> bool:
    """
    Check if a version satisfies a constraint.

    Args:
        version: Version string to check (e.g., "1.2.3")
        constraint: Constraint string (e.g., ">=1.0.0", "~=2.0.0", "^1.2.3")

    Returns:
        True if version satisfies constraint, False otherwise

    Raises:
        VersionConstraintError: If version or constraint is invalid
    """
    try:
        v = Version(version)
    except InvalidVersion as e:
        raise VersionConstraintError(f"Invalid version '{version}': {e}")

    try:
        parsed = parse_version_constraint(constraint)
        specifier_str = parsed["specifier"]
    except VersionConstraintError:
        raise

    try:
        specifier_set = SpecifierSet(specifier_str)
    except InvalidSpecifier as e:
        raise VersionConstraintError(f"Invalid specifier '{specifier_str}': {e}")

    return specifier_set.contains(v)


def parse_multiple_constraints(constraints: str) -> List[Dict]:
    """
    Parse multiple comma-separated constraints.

    Args:
        constraints: Comma-separated constraints (e.g., ">=1.0.0,<2.0.0")

    Returns:
        List of parsed constraint dictionaries

    Examples:
        >>> parse_multiple_constraints(">=1.0.0,<2.0.0")
        [{'operator': '>=', 'version': '1.0.0', 'specifier': '>=1.0.0'},
         {'operator': '<', 'version': '2.0.0', 'specifier': '<2.0.0'}]
    """
    if not constraints or not constraints.strip():
        return []

    parts = [c.strip() for c in constraints.split(",") if c.strip()]
    result = []
    for part in parts:
        result.append(parse_version_constraint(part))
    return result


def satisfies_all(version: str, constraints: str) -> bool:
    """
    Check if a version satisfies all comma-separated constraints.

    Args:
        version: Version string to check
        constraints: Comma-separated constraints (e.g., ">=1.0.0,<2.0.0" or "^1.2.3")

    Returns:
        True if version satisfies all constraints
    """
    if not constraints or not constraints.strip():
        return True

    try:
        v = Version(version)
    except InvalidVersion as e:
        raise VersionConstraintError(f"Invalid version '{version}': {e}")

    # Split on commas but allow whitespace
    parts = [p.strip() for p in constraints.split(",") if p.strip()]
    spec_parts = []
    try:
        for part in parts:
            parsed = parse_version_constraint(part)
            spec_parts.append(parsed["specifier"])
    except VersionConstraintError as e:
        raise VersionConstraintError(f"Invalid constraints '{constraints}': {e}")

    combined = ",".join(spec_parts)
    try:
        specifier_set = SpecifierSet(combined)
    except InvalidSpecifier as e:
        raise VersionConstraintError(f"Invalid constraints '{combined}': {e}")

    return specifier_set.contains(v)


def get_caret_range(version: str) -> Tuple[str, str]:
    """
    Get the min and max version for a caret range.

    Args:
        version: Base version (e.g., "1.2.3")

    Returns:
        Tuple of (min_version, max_version) as strings
    """
    try:
        v = Version(version)
    except InvalidVersion as e:
        raise VersionConstraintError(f"Invalid version '{version}': {e}")

    major = v.major
    minor = v.minor
    patch = v.micro

    if major == 0 and minor == 0:
        min_v = f"0.0.{patch}"
        max_v = f"0.0.{patch + 1}"
    elif major == 0:
        min_v = f"0.{minor}.{patch}"
        max_v = f"0.{minor + 1}.0"
    else:
        min_v = f"{major}.{minor}.{patch}"
        max_v = f"{major + 1}.0.0"

    return min_v, max_v


def get_tilde_range(version: str) -> Tuple[str, str]:
    """
    Get the min and max version for a tilde range.

    Args:
        version: Base version (e.g., "1.2.3")

    Returns:
        Tuple of (min_version, max_version) as strings
    """
    try:
        v = Version(version)
    except InvalidVersion as e:
        raise VersionConstraintError(f"Invalid version '{version}': {e}")

    major = v.major
    minor = v.minor
    patch = v.micro

    if major == 0:
        min_v = f"0.{minor}.{patch}"
        max_v = f"0.{minor + 1}.0"
    else:
        min_v = f"{major}.{minor}.{patch}"
        max_v = f"{major}.{minor + 1}.0"

    return min_v, max_v


# For backwards compatibility
def parse_constraint(constraint: str) -> Dict:
    """Alias for parse_version_constraint."""
    return parse_version_constraint(constraint)


def check_version(version: str, constraint: str) -> bool:
    """Alias for satisfies."""
    return satisfies(version, constraint)