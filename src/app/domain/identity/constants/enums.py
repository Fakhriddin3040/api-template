from enum import IntEnum


class ApiKeyStatusEnum(IntEnum):
    ACTIVE = 1
    INACTIVE = 2
    BLOCKED = 3


class OtpKindEnum(IntEnum):
    """What a one-time code is *for*.

    Values are append-only — they are persisted in ``identity_otp.kind`` and
    pinned by a CHECK constraint, so renumbering would silently reinterpret
    existing rows.
    """

    EMAIL_CONFIRMATION = 1
    FORGOT_PASSWORD = 3
