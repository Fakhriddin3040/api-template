from typing import (
    Protocol,
    Any,
    TypeVar,
    runtime_checkable,
    TYPE_CHECKING,
    Optional,
    Type,
    List,
)

from src.app.shared_kernel.types.base_types import T, ID_T

if TYPE_CHECKING:
    from src.app.shared_kernel.ports.domain.entity_proxy import EntityProxy

TEntityProxy = TypeVar("TEntityProxy")


@runtime_checkable
class EntitySourceProto(Protocol[T]):
    @property
    def source(self) -> T: ...
    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def has(self, key: str) -> bool: ...

    def set_related_entity(self, key: str, entity: Optional["EntityProxy"]) -> None: ...
    def get_related_entity(
        self, key: str, _: Type[TEntityProxy]
    ) -> TEntityProxy | None: ...
    def set_related_entities(self, key: str, entities: List["EntityProxy"]) -> None: ...
    def get_related_entities(
        self, key: str, _: Type[TEntityProxy]
    ) -> List[TEntityProxy]: ...
    def append_related_entity(self, key: str, entity: "EntityProxy") -> None:
        """Should append also when this object is not exists"""

    def remove_entity_from_collection(self, key: str, entity_id: ID_T) -> None: ...
    def build_root(self) -> T: ...
