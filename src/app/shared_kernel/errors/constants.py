from enum import IntEnum, StrEnum

from starlette import status


class AppExceptionStatusCodes(IntEnum):
    # AUTH
    INVALID_LOGIN_CREDENTIALS = 100
    INVALID_TOKEN_PROVIDED = 101
    ACCESS_TOKEN_REQUIRED = 102
    INVALID_PASSWORD = 103
    INVALID_OTP = 104
    OTP_ALREADY_VERIFIED = 105
    OTP_EXPIRED = 106
    INVALID_TOKEN_TYPE = 107
    INVALID_REFRESH_TOKEN = 108
    ACCESS_DENIED = 109
    UNAUTHORIZED = 110
    INVALID_ACCESS_TOKEN = 111
    OTP_RESEND_COOLDOWN = 112

    # VALIDATION
    UNIQUE_CONSTRAINT = 200
    DUPLICATED = 201
    REQUIRED_VALUE = 202
    STRING_RANGE_LIMIT_EXCEEDED = 203
    REGEX_NOT_MATCH = 204
    INVALID_TYPE = 205
    NUMERIC_RANGE_LIMIT_EXCEEDED = 206
    LIST_INVALID_RANGE = 207
    VALIDATION_ERROR = 208
    INVALID_VALUE = 209

    ## FILTERS
    REQUIRED_FILTER = 210
    INVALID_FILTER_LOOKUP = 211
    UNALLOWED_FILTER_LOOKUP = 212
    DUPLICATED_FILTER_FIELD = 213

    # FILES SPECIFIED
    FILE_SIZE_LIMIT_EXCEEDED = 300
    FILE_NOT_FOUND_IN_FS = 301
    UNSUPPORTED_FILE_FORMAT = 302
    INVALID_FILE_FORMAT = 303

    # ===== COMMON =====
    OBJECT_NOT_FOUND = 400
    REQUEST_BODY_IS_EMPTY = 401
    NOT_ENOUGH_STOCK = 402
    INVALID_INPUT = 403
    NOT_FOUND = 404
    RESOURCE_HAS_DEPENDENCIES = 411

    # ===== DOCUMENT SPECIFIED =====
    TOO_SHORT_CONTENT = 500

    # ===== UNKNOWN =====
    UNKNOWN_ERROR = 1900

    # SPECIAL_CASES
    DETAILED_ERROR = 10000
    NETWORK_ERROR = 10001
    UNEXPECTED_RESPONSE = 10002
    TIMEOUT = 10003


class AppExceptionMessage(StrEnum):
    NOT_FOUND = "Not found"
    ACCESS_TOKEN_REQUIRED = "Access token is not provided."
    INVALID_LOGIN_CREDENTIALS = "Invalid login credentials."
    INVALID_TOKEN_PROVIDED = "Invalid access key"
    INVALID_TOKEN_TYPE = "Invalid token type"
    FILE_SIZE_LIMIT_EXCEEDED = "File size limit exceeded"
    UNSUPPORTED_FILE_FORMAT = "Unsupported file format"
    INVALID_FILE_FORMAT = "Invalid file format"
    INVALID_VALUE = "Value format is invalid"
    FILE_NOT_FOUND_IN_FS = "File exists in database, but not found in file system"
    REQUEST_BODY_IS_EMPTY = "Request body is empty"
    UNIQUE_CONSTRAINT = "Unique constraint violated. One or more constraints violated"
    REQUIRED_VALUE = "Value is required"
    INVALID_OTP = "Invalid OTP provided"
    OTP_ALREADY_VERIFIED = "OTP has already been verified"
    OTP_EXPIRED = "OTP has expired"
    OTP_RESEND_COOLDOWN = "OTP was requested too recently"
    INVALID_PASSWORD = "Invalid password"
    LOGIN_REQUIRED = "Login required"
    ACCESS_DENIED = "Access denied"

    ## FILTERS
    REQUIRED_FILTER = "Filter required"
    INVALID_FILTER_LOOKUP = "Invalid filter lookup was provided"
    UNALLOWED_FILTER_LOOKUP = "Unallowed filter lookup was provided"
    DUPLICATED_FILTER_FIELD = "Filter field was duplicated"
    DUPLICATED_FILTER_VALUE = "Filter value was duplicated"

    # ===== UNKNOWN =====
    UNKNOWN_ERROR = "Unknown error"

    # ===== COMMON =====
    DETAILED_ERROR = "Detailed error. See details"

    # ===== DOCUMENT SPECIFIED =====
    TOO_SHORT_CONTENT = "File content is too short"

    def add_prefix(self, prefix: str) -> str:
        return f"{prefix.capitalize()} {self.value.lower()}"


class AppExceptionDetailPayloadKeys(StrEnum):
    # Location context for error
    LOCATION = "location"
    DUPLICATES = "duplicates"
    VALUE = "value"
    VALUES = "values"
    RANGES = "ranges"
    LOOKUP = "lookup"


class AppExceptionLocationEnum(StrEnum):
    QUERY_PARAMS = "query_params"
    BODY = "body"


class AppExceptionDetailCodes(StrEnum):
    CHAR_VALUE_DUPLICATED = "char_value_duplicated"
    CHAR_VALUE_COMBINATION_DUPLICATED = "char_value_combination_exists"
    CHAR_VALUE_NOT_FOUND = "char_value_not_found"
    IDENTIFIER_DUPLICATED = "identifier_duplicated"


AppExcStatusToHttpMap = {
    AppExceptionStatusCodes.OBJECT_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    AppExceptionStatusCodes.INVALID_LOGIN_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    AppExceptionStatusCodes.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    AppExceptionStatusCodes.ACCESS_DENIED: status.HTTP_403_FORBIDDEN,
}
