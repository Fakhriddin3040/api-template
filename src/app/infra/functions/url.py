"""Absolute-URL construction.

The public host lives in exactly one place — ``APP_DOMAIN`` — and the scheme is
derived from the environment, so there is no second variable that can disagree
with it.
"""

from dependency_injector.wiring import Provide, inject

from src.app.shared_kernel.config.app_config import AppConfig

__all__ = ["make_media_full_url", "make_full_url"]


@inject
def _config(app_config: AppConfig = Provide["config.app"]) -> AppConfig:
    return app_config


def make_full_url(path: str) -> str:
    """Absolute URL for a path relative to the host root."""
    return f"{_config().base_url}/{path.lstrip('/')}"


def make_media_full_url(path: str) -> str:
    """Absolute URL for a media path stored relative to the media root.

    Stored values look like ``images/thumbnail/x.webp``; nginx serves the media
    root at ``/media/``, so the root is re-added here rather than persisted.
    """
    return make_full_url(f"media/{path.lstrip('/')}")
