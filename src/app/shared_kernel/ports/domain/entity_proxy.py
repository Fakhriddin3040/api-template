from typing import Set, Dict, Any

from src.app.shared_kernel.ports.domain.entity_source_proto import EntitySourceProto


class EntityProxy:
    """
    Proxy entity properties to the source.
    The main reason of creating this class is ORM tracker can
    not work in not ORM models on update. Soo, the proxy will
    proxy changes into orm model or somewhere else.
    """

    __slots__ = ("_changed_fields", "_proxy_fields", "_source")

    _changed_fields: Set[str]
    _proxy_fields: Set[str]
    _source: EntitySourceProto

    def __init__(
        self,
        source: EntitySourceProto,
    ) -> None:
        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_changed_fields", set())

    @property
    def source(self) -> EntitySourceProto:
        return self._source

    def __setattr__(self, key, value):
        if key in self.__slots__:
            object.__setattr__(self, key, value)
            return

        if key in self._proxy_fields:
            old = self._source.get(key) if self._source.has(key) else None

            if old != value:
                self._source.set(key, value)
                self._changed_fields.add(key)

            return

        raise AttributeError(f"{self.__class__.__name__} has no attribute {key}")

    def __getattr__(self, key):
        if key in object.__getattribute__(self, "_proxy_fields"):
            return self._source.get(key)
        if key in object.__getattribute__(self, "__slots__"):
            return object.__getattribute__(self, key)
        raise AttributeError(f"{self.__class__.__name__} has no attribute {key}")

    @property
    def dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self._proxy_fields}

    def clear_changes(self):
        self._changed_fields.clear()

    def __hash__(self) -> int:
        return hash(self.id)
