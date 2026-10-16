"""Errors a served request answers with their own status (operonx ``http_status``, 1.27): the caller sent
something wrong. Any other exception in a run answers 500 with no detail."""


class BadRequest(ValueError):
    """The request's values are wrong (a date out of range): 400 with the message."""

    http_status = 400


class Conflict(ValueError):
    """The request is right but the state does not allow it now (inbox mode, a run already queued): 409."""

    http_status = 409
