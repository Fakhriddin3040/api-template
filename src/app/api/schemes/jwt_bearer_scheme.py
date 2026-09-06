from litestar import Request
from litestar.exceptions import HTTPException
from starlette import status

_BEARER_PREFIX = "Bearer "


class JWTBearer:
    """Pulls the raw token out of the Authorization header."""

    async def __call__(self, request: Request) -> str:
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header is missing",
            )

        if not auth_header.startswith(_BEARER_PREFIX):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization scheme, expected Bearer",
            )

        token = auth_header[len(_BEARER_PREFIX) :].strip()

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token is empty",
            )

        return token


jwt_token_scheme = JWTBearer()
