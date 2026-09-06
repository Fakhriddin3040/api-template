from typing import Protocol, Type, Any, runtime_checkable

from src.app.shared_kernel.ports.domain.entity_proxy import EntityProxy
from src.app.shared_kernel.ports.domain.entity_source_proto import EntitySourceProto


@runtime_checkable
class EntitySourceFactoryProto(Protocol):
    """
    Factory for 'EntitySource'
    Create an empty data source(db or some data storage) entity
    as a source for entity.
    """

    def empty(self, entity: Type[EntityProxy], **init_kwargs) -> EntitySourceProto:
        """Create an empty data source with given init kwargs."""

    def from_source(self, data_source: Any) -> EntitySourceProto:
        """Creates a data source from an existed object."""
