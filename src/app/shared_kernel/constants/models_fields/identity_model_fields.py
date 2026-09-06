from enum import StrEnum, auto

from src.app.shared_kernel.constants.enums import ModelFieldsBaseEnum


class UserField(ModelFieldsBaseEnum, StrEnum):
    """Field names of the user aggregate.

    The former ``UserProfile`` columns (first/last name, address, description,
    avatar) live here now — one user, one row, no profile side table.
    """

    ID = auto()
    PASSWORD = auto()
    EMAIL = auto()
    PHONE = auto()
    EMAIL_CONFIRMED = auto()
    IS_ACTIVE = auto()
    IS_SUPERUSER = auto()
    STATUS = auto()
    DATE_JOINED = auto()
    INFORMATION = auto()
    LAST_LOGIN_TIME = auto()
    CREATED_AT = auto()
    UPDATED_AT = auto()
    ACTIVATED_AT = auto()
    DEACTIVATED_AT = auto()
    ACTIVATED_BY = auto()
    DEACTIVATED_BY = auto()

    # Merged-in profile fields
    FIRST_NAME = auto()
    LAST_NAME = auto()
    ADDRESS = auto()
    DESCRIPTION = auto()
    AVATAR_ID = auto()

    @staticmethod
    def as_outref() -> str:
        return "user_id"


class OtpField(ModelFieldsBaseEnum, StrEnum):
    ID = auto()
    OTP = auto()
    CONTENT_ID = auto()
    CONTENT_TYPE = auto()
    KIND = auto()
    EXPIRES_AT = auto()
    USED_AT = auto()
    TARGET_VALUE = auto()
    VERIFIED = auto()


class ApiKeyField(ModelFieldsBaseEnum, StrEnum):
    ID = auto()
    KEY = auto()
    STATUS = auto()
    LAST_USED_AT = auto()
    OWNER_ID = auto()
