import msgspec

from src.app.shared_kernel.constants.enums import JwtPayload, JwtToken  # noqa: F401


class AccessTokenDTO(msgspec.Struct):
    access_token: str


class JwtTokenDTO(msgspec.Struct):
    access_token: str
    refresh_token: str
