from dataclasses import dataclass
from enum import StrEnum
from typing import List, Self, Optional

import regex
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


def _validate_ordering(v: str) -> str:
    if not regex.match(r"^-?[A-Za-z_]+(?:,-?[A-Za-z_]+)*$", v):
        raise ValueError("Ordering format is wrong")
    return v


class OrderingDirectionEnum(StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderingItem:
    direction: OrderingDirectionEnum
    field: str


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderingContainer:
    items: List[OrderingItem]

    @classmethod
    def from_str(cls, v: str) -> Optional[Self]:
        if not v:
            return None

        return cls(
            items=list(
                OrderingItem(
                    direction=(
                        OrderingDirectionEnum.DESC
                        if part.startswith("-")
                        else OrderingDirectionEnum.ASC
                    ),
                    field=part.lstrip("-"),
                )
                for part in v.split(",")
            )
        )

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        str_schema = core_schema.str_schema(
            max_length=100,
            strip_whitespace=True,
        )

        return core_schema.no_info_after_validator_function(
            cls.from_str,
            core_schema.no_info_after_validator_function(
                _validate_ordering, str_schema
            ),
        )
