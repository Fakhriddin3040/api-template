"""The ASGI application.

Pure Litestar — there is no second framework mounted behind it. Everything the
app needs is wired in `Bootstrap.init_di_containers()`, which runs at import time
so the DI wiring is in place before the first route is built.
"""

import logging
from contextlib import asynccontextmanager

from litestar import Litestar, Request, Router, get
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.middleware import DefineMiddleware
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.openapi.spec import Components, SecurityScheme, Server
from litestar.static_files import create_static_files_router

from src.app.api.deps.api_deps import get_mediator
from src.app.api.deps.context_deps import (
    get_current_user_from_request,
    get_execution_context,
)
from src.app.api.http.middlewares.deps_middleware import (
    AuthMiddleware,
    SessionDIMiddleware,
)
from src.app.api.http.middlewares.exception_middleware import exception_handler
from src.app.api.http.routers.health import healthcheck
from src.app.api.http.routers.v1 import blob_router, identity_router
from src.app.api.schemes.jwt_bearer_scheme import JWTBearer
from src.app.modules.filtering.litestar_integration import inject_filter_parameters
from src.app.modules.telemetry.integrations.litestar_middleware import (
    TelemetryMiddleware,
)
from src.app.modules.telemetry.logging import install_root_handler
from src.app.utils.environment.env_utils import DeploymentEnvironment
from src.bootstrap import Bootstrap

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"

Bootstrap.init_di_containers()

# Make sure plain `logging` calls in this process also land in the telemetry
# file sink the daemon tails.
install_root_handler("api")


@get("/get-schema", include_in_schema=False, security=[])
async def get_system_schema(request: Request) -> dict:
    """The generated OpenAPI document, as JSON."""
    return request.app.openapi_schema.to_schema()


@asynccontextmanager
async def lifespan(app: Litestar):
    await Bootstrap.bootstrap_async()
    logger.info("application started")
    yield
    logger.info("application shutting down")


def litestar_app_factory() -> Litestar:
    route_handlers = [
        healthcheck,
        get_system_schema,
        identity_router,
        blob_router,
    ]

    if DeploymentEnvironment.should_debug():
        # In production nginx serves /media directly; letting the app do it
        # would put every file download through the event loop.
        route_handlers.append(
            create_static_files_router(path="/media", directories=["media"])
        )

    return Litestar(
        debug=DeploymentEnvironment.should_debug(),
        path=API_PREFIX,
        exception_handlers={Exception: exception_handler},
        route_handlers=[Router(path="", route_handlers=route_handlers)],
        lifespan=[lifespan],
        cors_config=CORSConfig(
            allow_origins=DeploymentEnvironment.cors_allowed_origins(),
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        ),
        openapi_config=OpenAPIConfig(
            title="API Template",
            version="1.0.0",
            path="/docs",
            render_plugins=[SwaggerRenderPlugin(path="/swagger")],
            servers=[Server(url=API_PREFIX, description="API Template")],
            components=Components(
                security_schemes={
                    "bearer": SecurityScheme(
                        type="http",
                        scheme="bearer",
                        bearer_format="JWT",
                        description="JWT Bearer Authentication",
                    )
                }
            ),
        ),
        middleware=[
            # Order matters: the session must exist before AuthMiddleware
            # resolves the user out of the database.
            DefineMiddleware(SessionDIMiddleware),
            DefineMiddleware(AuthMiddleware),
            DefineMiddleware(TelemetryMiddleware),
        ],
        security=({"bearer": []},),
        dependencies={
            "mediator": Provide(get_mediator),
            "jwt_bearer_scheme": Provide(JWTBearer, sync_to_thread=False),
            "ex_ctx": Provide(get_execution_context),
            # Maybe user
            "muser": Provide(get_current_user_from_request(required=False)),
            # Required user
            "user": Provide(get_current_user_from_request(required=True)),
            # Required user, API key accepted as well as a bearer token
            "apik_user": Provide(
                get_current_user_from_request(required=True, allow_api_key_access=True)
            ),
        },
    )


app = litestar_app_factory()
inject_filter_parameters(app)
