from enum import IntEnum, StrEnum


class StatusEnum(IntEnum):
    ACTIVE = 1
    INACTIVE = 0


class ContentTypeEnum(StrEnum):
    """What an OTP (or any polymorphic row) points at.

    Values are the physical table names, so a row stays readable straight from
    the database. Append-only: they are persisted.
    """

    USER = "identity_user"
