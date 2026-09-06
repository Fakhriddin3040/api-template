"""Public hostnames for the deployment.

Read from the environment rather than hardcoded per stage: a template has no
idea what any given fork's hosts are called.

Both are bare hosts (no scheme, no trailing slash); the helpers that build URLs
add those, so callers can't accidentally produce a double slash.

The scheme follows the environment — a local server has no TLS, so hardcoding
https there would emit links that simply do not resolve.
"""

import os

from src.app.utils.environment.env_utils import DeploymentEnvironment

SCHEME = "http" if DeploymentEnvironment.is_local() else "https"

BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost:8000")
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "localhost:3000")


def backend_url(path: str) -> str:
    """Absolute backend URL for a path relative to the host root."""
    return f"{SCHEME}://{BACKEND_HOST}/{path.lstrip('/')}"


def frontend_url(path: str) -> str:
    """Absolute frontend URL for a path relative to the host root."""
    return f"{SCHEME}://{FRONTEND_HOST}/{path.lstrip('/')}"
