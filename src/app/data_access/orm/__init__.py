"""ORM package.

Importing `models` here is what guarantees SQLAlchemy can configure its mappers:
`UserOrmModel.avatar` and the `AuthorInfoModelMixin` relationships reference each
other by *name*, so both classes must exist before the first mapper runs. Without
this, importing one model alone (a test, a script) fails at query time with
"failed to locate a name".
"""

from . import event_listeners, models

__all__ = ["event_listeners", "models"]
