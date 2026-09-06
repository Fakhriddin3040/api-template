from typing import Protocol, runtime_checkable

from src.app.shared_kernel.ports.result import ResultDetailed
from src.app.shared_kernel.types.jwt_schemas import JwtTokenDTO


@runtime_checkable
class AuthServiceProto(Protocol):
    async def login(self, *, email: str, password: str) -> ResultDetailed[JwtTokenDTO]:
        """Exchange credentials for a token pair.

        Every failure — unknown address, wrong password, unconfirmed or disabled
        account — answers with the same error, so the endpoint cannot be used to
        discover which addresses are registered.
        """

    async def refresh(self, *, refresh_token: str) -> ResultDetailed[JwtTokenDTO]:
        """Rotate a refresh token into a fresh pair."""
