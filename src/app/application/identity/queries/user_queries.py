from typing import Annotated, Optional

from src.app.shared_kernel.params.list_queries import ShortListQuery  # noqa: F401
from src.app.shared_kernel.params.ordering import OrderingContainer  # noqa: F401
from src.app.shared_kernel.params.query_mixins import OrderingQueryMixin
from src.app.shared_kernel.pydantic.types import ListQuery, Query
from src.app.shared_kernel.types.api_annotated import ATSearch
from src.app.shared_kernel.types.common_annotated import ATDatetimeRN
from src.app.shared_kernel.types.filter_specs import AFStatus
from src.app.shared_kernel.types.ordering_types import OrderingAllowedFieldsT
from src.app.modules.filtering.meta import FilterMeta, FilterSpec
from src.app.shared_kernel.types.base_types import ID_T


class UserListQuery(ListQuery, OrderingQueryMixin, metaclass=FilterMeta):
    _ordering_allowed_fields: OrderingAllowedFieldsT = {"created_at", "email"}

    # Compiles against email + first/last name — see UserFilterCompiler.
    search: Annotated[Optional[ATSearch], FilterSpec.string()] = None

    status: AFStatus

    created_at__rn: ATDatetimeRN


class UserDetailedQuery(Query):
    id: ID_T


class MeQuery(Query):
    """The caller's own record; the id comes from the token, never the request."""

    id: ID_T
