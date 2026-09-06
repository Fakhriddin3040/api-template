"""Cache key construction.

Every key is built here rather than inline at call sites, so the namespace stays
visible in one place and an invalidation can never miss a variant someone
spelled differently.
"""

from src.app.shared_kernel.types.base_types import ID_T

NAMESPACE = "app"


def user_key(user_id: ID_T) -> str:
    return f"{NAMESPACE}:user:{user_id}"


def build(*parts: str | ID_T) -> str:
    """Join arbitrary parts into a namespaced key."""
    return ":".join((NAMESPACE, *(str(p) for p in parts)))
