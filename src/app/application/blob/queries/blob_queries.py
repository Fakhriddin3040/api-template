from src.app.shared_kernel.pydantic.types import ListQuery, Query
from src.app.shared_kernel.types.base_types import ID_T


class BlobListQuery(ListQuery): ...


class BlobByIdQuery(Query):
    id: ID_T
