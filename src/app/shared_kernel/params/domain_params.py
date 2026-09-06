from pydantic import BaseModel, ConfigDict


class DomainParams(BaseModel):
    """Input to a domain operation, valid by construction.

    Pydantic does the validating: by the time an aggregate receives one of these,
    every field has already been checked, so the aggregate holds invariants that
    span fields rather than re-checking each one. A malformed value raises
    ``ValidationError`` at construction, which the exception middleware renders
    as a 422.

    ``frozen`` because a params object is a message, not state — mutating one
    after an aggregate has read it would be a silent lie. ``extra="forbid"``
    because these are built in our own code: an unknown key is a typo, and
    accepting it silently is how a renamed field ends up quietly ignored.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
