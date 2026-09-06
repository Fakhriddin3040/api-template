import base64

from litestar import Request
from litestar.exceptions import HTTPException
from litestar.types import Scope, Receive, Send, ASGIApp

from starlette import status
from urllib3.util import Url

from src.app.api.deps.context_deps import (
    get_current_user_from_token,
    get_api_key_object,
)
from src.app.infra.constants import API_KEY_HEADER
from src.app.infra.globals import DIContainerRegistry
from src.app.shared_kernel.providers.execution_context_provider import (
    ExecutionContextProvider,
)
from src.app.shared_kernel.types.execution_context import ExecutionContextRequest


class SessionDIMiddleware:
    """
    Must be the first middleware to init the db session for the next middlewares could use the db session
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        token = DIContainerRegistry.get_root_container().db.set_current_session()

        try:
            await self.app(scope, receive, send)
        finally:
            await DIContainerRegistry.get_root_container().db.clear_current_session(
                token=token
            )


class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        jwt = request.headers.get("Authorization")

        # Api key in base64 format
        api_key = request.headers.get(API_KEY_HEADER)
        user = None

        if jwt and api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either API key or bearer token, not both",
            )

        if jwt:
            parts = jwt.strip().split(" ")
            if len(parts) == 2:
                token = parts[1]
                user = await get_current_user_from_token(token=token)
        elif api_key:
            try:
                api_key = base64.b64decode(api_key)
            except (ValueError, TypeError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Provided invalid api_key",
                ) from exc

            api_key_obj = await get_api_key_object(api_key)
            scope.setdefault("state", {})["api_key_obj"] = api_key_obj
            user = api_key_obj.owner if api_key_obj is not None else None

        scope.setdefault("state", {})["user"] = user
        ctx_token = ExecutionContextProvider.create(
            user=user,
            **dict(
                request=ExecutionContextRequest(
                    url=Url(
                        scheme=scope.get("scheme", "https"),
                        host=scope["server"][0],
                        port=scope["server"][1],
                        path=scope["path"],
                        query=scope["query_string"].decode("latin-1"),
                    )
                )
            ),
        )[1]
        try:
            await self.app(scope, receive, send)
        finally:
            ExecutionContextProvider.clear(token=ctx_token)
