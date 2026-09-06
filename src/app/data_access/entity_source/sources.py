from itertools import chain
from typing import Any, List, Type, TypeVar, Optional, Dict, Iterable, Tuple

from src.app.shared_kernel.ports.domain.entity_proxy import EntityProxy
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)
from src.app.data_access.orm.base.base_orm_models import SqlAlchemyBaseModel
from src.app.shared_kernel.ports.domain.entity_source_proto import (
    EntitySourceProto,
    TEntityProxy,
)

T = TypeVar("T", bound=EntityProxy)


class SqlAlchemyEntitySource(EntitySourceProto[SqlAlchemyBaseModel]):
    def __init__(self, obj: SqlAlchemyBaseModel):
        self._obj = obj
        self._related_entities: Dict[str, Optional[EntityProxy]] = {}
        self._related_entities_collections: Dict[str, List[EntityProxy]] = {}

    def set(self, key: str, value: Any) -> None:
        return setattr(self._obj, key, value)

    def has(self, key: str) -> bool:
        return hasattr(self._obj, key)

    def get(self, key: str) -> Any:
        return getattr(self._obj, key)

    @property
    def source(self) -> SqlAlchemyBaseModel:
        return self._obj

    def set_related_entity(self, key: str, entity: Optional[EntityProxy]) -> None:
        self._related_entities[key] = entity
        setattr(self._obj, key, entity.source.source)

    def set_related_entities(self, key: str, entities: List[EntityProxy]) -> None:
        self._related_entities_collections[key] = entities
        setattr(self._obj, key, [e.source.build_root() for e in entities])

    def get_related_entity(self, key: str, _: Type[TEntityProxy]) -> EntityProxy | None:
        return self._related_entities.get(key, None)

    def append_related_entity(self, key: str, entity: EntityProxy) -> None:
        if key not in self._related_entities_collections:
            self._related_entities_collections[key] = [entity]
            setattr(self._obj, key, [entity.source.build_root()])
        else:
            self._related_entities_collections[key].append(entity)
            getattr(self._obj, key).append(entity.source.build_root())

    def get_related_entities(
        self, key: str, _: Type[TEntityProxy]
    ) -> List[TEntityProxy]:
        return self._related_entities_collections.get(key, [])

    def build_root(self) -> SqlAlchemyBaseModel:
        _chain: Iterable[Tuple[str, EntityProxy | List[EntityProxy] | None]] = chain(
            self._related_entities.items(), self._related_entities_collections.items()
        )

        for key, value in _chain:
            if value is None:
                setattr(self.source, key, None)

            elif isinstance(value, EntityProxy):
                setattr(self.source, key, value.source.build_root())

            elif isinstance(value, list):
                setattr(
                    self.source, key, [entity.source.build_root() for entity in value]
                )

        return self.source

    def remove_entity_from_collection(self, key: str, entity_id: ID_T) -> None:
        if key in self._related_entities_collections:
            new_col = [
                entity
                for entity in self._related_entities_collections[key]
                if entity.source.get("id") != entity_id
            ]
            self._related_entities_collections[key] = new_col

            setattr(self._obj, key, [e.source.build_root() for e in new_col])


ensure_isimplementation(SqlAlchemyEntitySource, EntitySourceProto)
