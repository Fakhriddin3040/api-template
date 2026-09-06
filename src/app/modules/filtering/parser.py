from typing import Iterable, List, Optional

from pydantic import BaseModel

from src.app.modules.filtering.types import (
    FilterSpec,
    FilterContainerCollection,
    FilterContainer,
)

FIELD_LOOKUP_SEPARATOR = "__"
RANGE_SEPARATOR = ","


class PydanticFilterParser:
    """Filter for parsing object which contains
    collection of FilterSpec to FilterContainers"""

    @staticmethod
    def extract_spec(metadata: Iterable) -> Optional[FilterSpec]:
        # The spec is carried either bare or on a pipeline-injector's `.spec`
        # (the injector, not the dataclass, lives in the annotation metadata so
        # that Litestar's OpenAPI generator doesn't try to document FilterSpec).
        for meta in metadata:
            if isinstance(meta, FilterSpec):
                return meta

            candidate = getattr(meta, "spec", None)
            if isinstance(candidate, FilterSpec):
                return candidate

        return None

    @classmethod
    def parse(cls, obj: BaseModel) -> FilterContainerCollection:
        """Parses obj to FilterContainer"""
        res: List[FilterContainer] = []

        for name, info in type(obj).model_fields.items():
            spec = cls.extract_spec(info.metadata)

            if spec is None:
                continue

            v = getattr(obj, name)

            # Don't handle `IS NULL` causes right now
            if v is None:
                continue

            res.append(
                FilterContainer(
                    value=v,
                    field=spec.field or name.split(FIELD_LOOKUP_SEPARATOR)[0],
                    lookup=spec.lookup,
                )
            )

        return tuple(res)


def parse_filters(obj: BaseModel) -> FilterContainerCollection:
    return PydanticFilterParser.parse(obj)
