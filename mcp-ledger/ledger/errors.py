"""Failures that prevent a ledger operation from committing."""


class SheetNotFoundError(Exception):
    """The requested sheet does not exist in the authorised workbook."""


class RevisionConflictError(Exception):
    """The sheet changed after the operation's source snapshot."""


class IdempotencyConflictError(Exception):
    """An operation key already belongs to a different request."""
