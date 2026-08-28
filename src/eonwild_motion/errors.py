class MotionError(RuntimeError):
    """A fail-closed engine or contract error."""


class ContractError(MotionError):
    """A schema, reference, or semantic contract error."""


class ValidationFailure(MotionError):
    """A candidate failed one or more release gates."""
