from datetime import datetime
from enum import StrEnum, auto

from pydantic import BaseModel

from src.app.shared_kernel.types.base_types import ID_T


class ModelFieldsBaseEnum(StrEnum):
    @property
    def as_foreign_key(self) -> str:
        """Return the foreign key field name for the given field."""
        return f"{self.value}_id"

    @staticmethod
    def as_outref() -> str: ...


class JwtType(StrEnum):
    ACCESS_TOKEN = "access"
    REFRESH_TOKEN = "refresh"


class JwtKeys(StrEnum):
    IAT = auto()
    EXP = auto()
    ALG = auto()
    TYP = auto()
    JTI = auto()
    LAST_LOGIN_TIME = auto()
    TOKEN_TYPE = auto()


class JwtPayload(BaseModel):
    token_type: JwtType = None
    exp: int = None
    iat: int = None
    jti: str = None
    user_id: ID_T = None
    last_login_time: datetime = None


class JwtToken(BaseModel):
    access_token: str
    refresh_token: str
