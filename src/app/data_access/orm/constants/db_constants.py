from enum import StrEnum

from src.app.shared_kernel.constants import entity_common_const


class DatabaseTable(StrEnum):
    """Every physical table name, prefixed by its bounded context.

    The prefix is what keeps two contexts from colliding on a generic name
    (`user`, `file`, `link`) as the schema grows.
    """

    # IDENTITY
    USER = "identity_user"
    OTP = "identity_otp"
    API_KEY = "identity_api_key"

    # BLOB
    BLOB_OBJECT = "blob_object"

    # TELEMETRY
    TELEMETRY_LOG = "telemetry_log"
    TELEMETRY_LOG_TRACEBACK = "telemetry_log_traceback"

    @property
    def as_foreign_key(self) -> str:
        return f"{self.value}.id"


# Postgres object limited name length
MAX_DB_IDENTIFIER_LENGTH = 63


def db_identifier(name: str, *, max_length: int = MAX_DB_IDENTIFIER_LENGTH) -> str:
    if len(name) <= max_length:
        return name

    # Deterministic shortening: keep a readable prefix and append a hash suffix.
    # This prevents collisions when different long names share the same prefix.
    import hashlib

    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    prefix_length = max_length - (2 + len(digest))  # "__" + digest
    return f"{name[:prefix_length]}__{digest}"


BALANCE_DECIMAL_ARGS = {
    "precision": entity_common_const.DECIMAL_BALANCE_DIGITS,
    "scale": entity_common_const.DECIMAL_BALANCE_PLACES,
}

LONG_DECIMAL_ARGS = {
    "precision": entity_common_const.LONG_DECIMAL_DIGITS,
    "scale": entity_common_const.LONG_DECIMAL_PLACES,
}

DECIMAL_PRICE_ARGS = {
    "precision": entity_common_const.DECIMAL_PRICE_DIGITS,
    "scale": entity_common_const.DECIMAL_PRICE_PLACES,
}
