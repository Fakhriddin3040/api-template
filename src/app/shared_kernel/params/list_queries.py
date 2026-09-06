from typing import Annotated, Optional

from src.app.shared_kernel.pydantic.types import ListQuery
from src.app.shared_kernel.types.api_annotated import ATSearch
from src.app.shared_kernel.types.filter_specs import AFStatus
from src.app.modules.filtering.meta import FilterMeta, FilterSpec


class ShortListQuery(ListQuery, metaclass=FilterMeta):
    """Base query for `/short` reference endpoints:
    limit/offset + optional prefix search + status filter.

    Note: `Optional[AFSearch]` is not used here on purpose — wrapping
    `Annotated` into `Optional` hides `FilterSpec` from both `FilterMeta`
    and the filter parser, so such a field never compiles into a filter.
    """

    search: Annotated[Optional[ATSearch], FilterSpec.string()] = None
    status: AFStatus
