from typing import Optional, Protocol, runtime_checkable

from src.app.infra.constants.enums.jwt_enums import JwtType
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.types.entities import UserBase
from src.app.shared_kernel.types.jwt_schemas import (
    AccessTokenDTO,
    JwtPayload,
    JwtToken,
)


@runtime_checkable
class JwtProviderProto(Protocol):
    def for_user(self, user: UserBase) -> JwtToken: ...
    def generate_token(self, payload: JwtPayload) -> str: ...
    def is_valid_access_token(self, access_token: str) -> bool: ...
    def refresh_access_token(self, token: str) -> Optional[AccessTokenDTO]: ...
    def decode_payload(self, token: bytes | str) -> Optional[JwtPayload]: ...
    @classmethod
    def get_payload(
        cls,
        expire: int | float,
        token_type: JwtType,
        user_id: ID_T,
    ) -> JwtPayload: ...
