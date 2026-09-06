import json
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Type, Optional, get_args, get_origin

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

from src.app.modules.filtering.enums import FilterLookupEnum
from src.app.modules.filtering.types import FilterSpec
from src.app.modules.filtering.validator import FilterValidator

RANGE_SEPARATOR = ","


def _split_range(value: Any) -> Any:
    """`"low,high"` -> `(low|None, high|None)`; anything else passes through
    untouched for the tuple schema to accept or reject."""
    if not isinstance(value, str):
        return value

    parts = value.split(RANGE_SEPARATOR)
    if len(parts) != 2:
        return value

    return tuple(part.strip() or None for part in parts)


def _split_collection(value: Any) -> Any:
    """`"value, ..."` -> `value, ...`; anything else passes through
    untouched for the tuple schema to accept or reject."""
    if not isinstance(value, str):
        return value

    return value.split(RANGE_SEPARATOR)


def _parse_json(value: Any) -> Any:
    """Decodes a JSON string into its Python value; anything else (an already
    parsed list, from a body or direct construction) passes through for the
    list schema to accept or reject.

    A malformed string is passed through untouched rather than raised on, so the
    caller gets the list schema's "expected list" error instead of a bare
    JSONDecodeError leaking out of the pipeline.
    """
    if not isinstance(value, str):
        return value

    try:
        return json.loads(value)
    except ValueError:
        return value


def _json_number(value: Any) -> Any:
    """Decimal is not JSON-serializable; render it as int/float for the schema."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


class FilterPipelineInjector:
    def __init__(self, spec: FilterSpec) -> None:
        self.spec = spec

    def _validate(self, value: Any) -> Any:
        FilterValidator.validate(spec=self.spec, value=value)
        return value

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        if self.spec.lookup == FilterLookupEnum.RANGE:
            value_schema = self._range_value_schema(handler)
        elif self.spec.lookup == FilterLookupEnum.IN:
            value_schema = self._collection_value_schema(handler)
        elif self.spec.lookup == FilterLookupEnum.JSON:
            value_schema = self._json_value_schema(handler)
        else:
            value_schema = handler(self.spec.base_type)

        schema = core_schema.chain_schema(
            [
                value_schema,
                core_schema.no_info_plain_validator_function(self._validate),
            ]
        )

        if not self.spec.required:
            schema = core_schema.nullable_schema(schema)

        return schema

    def _range_value_schema(
        self, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        endpoint = core_schema.nullable_schema(handler(self._get_base_type()))
        pair = core_schema.tuple_positional_schema([endpoint, endpoint])
        return core_schema.no_info_before_validator_function(_split_range, pair)

    def _collection_value_schema(
        self, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        endpoint = core_schema.nullable_schema(handler(self._get_base_type()))
        pair = core_schema.tuple_variable_schema(endpoint)
        return core_schema.no_info_before_validator_function(_split_collection, pair)

    def _json_value_schema(
        self, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """A JSON array of `base_type`, accepted either already-parsed (POST
        body / direct construction) or as a raw JSON string (query param)."""
        # `max_length` is left to `FilterValidator` so an over-long payload
        # reports as an AppException detail like every other filter, rather than
        # as a raw pydantic error.
        items = core_schema.tuple_variable_schema(handler(self._get_base_type()))
        return core_schema.no_info_before_validator_function(_parse_json, items)

    def _get_base_type(self) -> Any:
        from src.app.shared_kernel.types.common_annotated import ATDatetime

        if self.spec.base_type is datetime:
            return ATDatetime
        return self.spec.base_type

    def __get_pydantic_json_schema__(
        self, core_schema_: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema = handler(core_schema_)
        spec = self.spec

        target = schema
        if "anyOf" in schema:
            target = next(
                (s for s in schema["anyOf"] if s.get("type") != "null"),
                schema,
            )
        if spec.description:
            schema["description"] = spec.description

        if _is_number(spec.gt):
            target["exclusiveMinimum"] = _json_number(spec.gt)
        if _is_number(spec.gte):
            target["minimum"] = _json_number(spec.gte)
        if _is_number(spec.lt):
            target["exclusiveMaximum"] = _json_number(spec.lt)
        if _is_number(spec.lte):
            target["maximum"] = _json_number(spec.lte)

        # A JSON filter's length bound counts *items*, not characters, so it
        # renders as minItems/maxItems. Emitting minLength/maxLength here would
        # tell a client the whole payload must be <= N characters long.
        if spec.lookup == FilterLookupEnum.JSON:
            if spec.min_length is not None:
                target["minItems"] = spec.min_length
            if spec.max_length is not None:
                target["maxItems"] = spec.max_length

            return schema

        if spec.min_length is not None:
            target["minLength"] = spec.min_length
        if spec.max_length is not None:
            target["maxLength"] = spec.max_length

        is_enum_type = isinstance(spec.base_type, type) and issubclass(
            spec.base_type, Enum
        )
        if spec.choices is not None and not is_enum_type:
            target["enum"] = [
                c.value if isinstance(c, Enum) else _json_number(c)
                for c in spec.choices
            ]

        return schema


class FilterMeta(ModelMetaclass):
    @staticmethod
    def _extract_spec(annotation: Any) -> Optional[FilterSpec]:
        if isinstance(annotation, FilterSpec):
            return annotation

        if get_origin(annotation) is Annotated:
            for meta in get_args(annotation)[1:]:
                if isinstance(meta, FilterSpec):
                    return meta
        return None

    def __new__(mcs, name, bases, namespace, **kwargs) -> Type:
        annotations = namespace.get("__annotations__", {})

        for field_name, annotation in list(annotations.items()):
            spec = mcs._extract_spec(annotation)

            if spec is None:
                continue

            if get_origin(annotation) is Annotated:
                base, *metadata = get_args(annotation)

                metadata = [m for m in metadata if not isinstance(m, FilterSpec)]
            else:
                base, metadata = spec.base_type, []

            if spec.field is None:
                spec = replace(spec, field=field_name.split("__")[0])

            # Don't leave FilterSpec only as a type. Need to wrap into annotated so
            # litestar will not try to render a doc for it.
            annotations[field_name] = Annotated[
                (base, *metadata, FilterPipelineInjector(spec))
            ]

            if spec.required:
                namespace.pop(field_name, None)

            else:
                namespace[field_name] = None

        namespace["__annotations__"] = annotations
        return super().__new__(mcs, name, bases, namespace, **kwargs)
