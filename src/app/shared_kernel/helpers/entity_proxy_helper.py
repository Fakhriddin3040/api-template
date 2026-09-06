from typing import List, Any
from src.app.shared_kernel.ports.domain.entity_proxy import EntityProxy


class EntityProxyHelper:
    @staticmethod
    def get_data_source(proxy: EntityProxy) -> Any:
        return proxy.source.source

    @staticmethod
    def get_data_sources(proxies: List[EntityProxy]) -> List:
        return [item.source.source for item in proxies]
