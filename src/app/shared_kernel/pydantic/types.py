from typing import Generic, List

import msgspec
from pydantic import BaseModel, ConfigDict, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema

from src.app.shared_kernel.constants import api_const
from src.app.shared_kernel.types.base_types import T


class BasePydanticModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)


class Command(BaseModel):
    """Base class for mediator commands (write side)."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore", frozen=True)


class Query(BaseModel):
    """The same contract as ``Command``, but for read-only (GET) requests."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")


class ListQuery(Query):
    limit: int = Field(
        default=api_const.DEFAULT_LIMIT,
        gt=api_const.MIN_LIMIT - 1,
        lt=api_const.MAX_LIMIT + 1,
    )
    offset: int = Field(default=api_const.DEFAULT_OFFSET, gt=api_const.MIN_OFFSET - 1)

    model_config = ConfigDict(extra="ignore")

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        schema = handler(core_schema)

        properties = schema.setdefault("properties", {})

        if "limit" in properties:
            properties["limit"].update(
                {
                    "title": "Limit",
                    "description": (
                        f"Maximum number of items to return. "
                        f"Allowed range: {api_const.MIN_LIMIT}-{api_const.MAX_LIMIT}. "
                        f"Default: {api_const.DEFAULT_LIMIT}."
                    ),
                    "example": api_const.DEFAULT_LIMIT,
                }
            )

        if "offset" in properties:
            properties["offset"].update(
                {
                    "title": "Offset",
                    "description": (
                        "Number of items to skip before returning results. "
                        f"Minimum: {api_const.MIN_OFFSET}. "
                        f"Default: {api_const.DEFAULT_OFFSET}."
                    ),
                    "example": api_const.DEFAULT_OFFSET,
                }
            )

        return schema


class ListQueryResponse(msgspec.Struct, Generic[T]):
    count: int
    rows: List[T]
