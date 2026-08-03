"""Compliance engine exception types."""


class ComplianceError(Exception):
    """Base exception for all compliance engine errors."""
    pass


class CheckNotFoundError(ComplianceError):
    """A requested check was not found in the registry."""

    def __init__(self, check_id: str):
        super().__init__("Check '%s' not found in registry" % check_id)
        self.check_id = check_id


class DuplicateCheckError(ComplianceError):
    """A check with this ID is already registered."""

    def __init__(self, check_id: str):
        super().__init__("Check '%s' is already registered" % check_id)
        self.check_id = check_id


class CheckExecutionError(ComplianceError):
    """A check's execution function raised an error."""

    def __init__(self, check_id: str, original_error: str = ""):
        msg = "Check '%s' execution failed" % check_id
        if original_error:
            msg += ": %s" % original_error
        super().__init__(msg)
        self.check_id = check_id
        self.original_error = original_error


class InvalidSessionStateError(ComplianceError):
    """Operation requested in an invalid session state."""

    def __init__(self, current_state: str, expected_states: str):
        super().__init__(
            "Invalid session state '%s'. Expected one of: %s" % (
                current_state, expected_states
            )
        )
        self.current_state = current_state
        self.expected_states = expected_states


class SessionImmutableError(ComplianceError):
    """Attempted to modify an immutable (completed/archived) session."""

    def __init__(self, session_id: str):
        super().__init__(
            "Session '%s' is immutable (already in terminal state)" % session_id
        )
        self.session_id = session_id


class VerdictComputationError(ComplianceError):
    """Error during verdict computation."""

    def __init__(self, reason: str):
        super().__init__("Verdict computation failed: %s" % reason)
        self.reason = reason


class RegistryError(ComplianceError):
    """Error during registry operations."""

    def __init__(self, reason: str):
        super().__init__("Registry error: %s" % reason)
        self.reason = reason


class EvidenceCollectionError(ComplianceError):
    """Error during evidence collection."""

    def __init__(self, check_id: str, reason: str):
        super().__init__("Evidence collection failed for '%s': %s" % (check_id, reason))
        self.check_id = check_id
        self.reason = reason


class ReportGenerationError(ComplianceError):
    """Error during report generation."""

    def __init__(self, reason: str):
        super().__init__("Report generation failed: %s" % reason)
        self.reason = reason


class LifecycleError(ComplianceError):
    """Error during lifecycle state transition."""

    def __init__(self, reason: str):
        super().__init__("Lifecycle error: %s" % reason)
        self.reason = reason
