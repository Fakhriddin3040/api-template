from litestar import Router

from src.app.api.http.routers.v1.identity.auth_api import AuthController
from src.app.api.http.routers.v1.identity.forgot_api import ForgotPasswordController
from src.app.api.http.routers.v1.identity.user_api import UserController

identity_router = Router(
    path="/identity",
    route_handlers=[
        Router(path="/auth", route_handlers=[AuthController], tags=["Auth"]),
        Router(
            path="/auth/forgot-password",
            route_handlers=[ForgotPasswordController],
            tags=["Forgot password"],
        ),
        Router(path="/users", route_handlers=[UserController], tags=["Users"]),
    ],
)

__all__ = ["identity_router"]
