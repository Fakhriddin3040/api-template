from src.app.shared_kernel.constants.host_const import BACKEND_HOST, backend_url

__all__ = ["BACKEND_HOST", "make_media_full_url"]


def make_media_full_url(path: str) -> str:
    """Absolute URL for a media path stored relative to the media root.

    Stored values look like ``images/original/x.jpg``; nginx serves the media
    root at ``/media/``, so the root is re-added here rather than persisted.
    """
    return backend_url(f"media/{path.lstrip('/')}")
