from enum import StrEnum


class JwtType(StrEnum):
    ACCESS_TOKEN = "access"
    REFRESH_TOKEN = "refresh"
