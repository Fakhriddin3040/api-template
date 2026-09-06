import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum, StrEnum

from src.app.shared_kernel.params.query_mixins import OrderingQueryMixin
from types import UnionType
from typing import AbstractSet, Any, List, TypeVar, Union, get_args, get_origin, Type

from src.app.shared_kernel.pydantic.types import Query
from litestar import Litestar, Request
from litestar.di import Provide
from litestar.exceptions import ValidationException
from litestar.handlers import HTTPRouteHandler
from litestar.routes import HTTPRoute
from litestar.openapi.spec import Parameter, Schema
from litestar.openapi.spec.enums import OpenAPIType
from pydantic import BaseModel, ValidationError

from src.app.modules.filtering.enums import FilterLookupEnum
from src.app.modules.filtering.parser import PydanticFilterParser
from src.app.modules.filtering.types import FilterSpec
from src.app.modules.filtering.meta import FilterMeta

_PY_TO_OPENAPI = {
    Decimal: (OpenAPIType.NUMBER, None),
    int: (OpenAPIType.INTEGER, None),
    float: (OpenAPIType.NUMBER, None),
    bool: (OpenAPIType.BOOLEAN, None),
    date: (OpenAPIType.STRING, "date"),
    datetime: (OpenAPIType.STRING, "date-time"),
    str: (OpenAPIType.STRING, None),
}

# Stand-in values used to render a JSON filter's example payload.
_JSON_PLACEHOLDERS: dict[Any, Any] = {
    int: 1,
    Decimal: 1,
    float: 1.0,
    bool: True,
    str: "value",
    date: "2026-01-31",
    datetime: "2026-01-31T12:00:00Z",
}


class LitestarOptKeyEnum(StrEnum):
    FILTER_SPECS = "filter_specs"


def _to_number(value: Any) -> Any:
    """Decimal isn't JSON-serializable in the schema; render it as int/float."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def _unwrap(annotation: Any) -> Any:
    """Strip Optional/Union[..., None] and Annotated down to the core type."""
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return _unwrap(non_none[0])
    if hasattr(annotation, "__metadata__"):  # Annotated[T, ...]
        return _unwrap(get_args(annotation)[0])
    return annotation


def _is_structured(annotation: Any) -> bool:
    """True for a nested model, or a collection of them.

    A query string can carry scalars and flat lists of scalars, nothing more, so
    such a field can only have arrived in the request body (see the body merge in
    `path_bound_query`). Documenting it as a query parameter would advertise a
    shape no client can actually send.
    """
    base = _unwrap(annotation)

    if isinstance(base, type) and issubclass(base, BaseModel):
        return True

    if get_origin(base) is not None:
        return any(_is_structured(arg) for arg in get_args(base))

    return False


def _enum_schema(enum_type: type[Enum]) -> Schema:
    members = [m.value for m in enum_type]
    otype = (
        OpenAPIType.INTEGER
        if all(isinstance(v, int) for v in members)
        else OpenAPIType.STRING
    )
    return Schema(type=otype, enum=members)


def _json_example(base: Any) -> str:
    """A concrete one-element payload for a JSON filter.

    Built from the item model's own fields so the example stays correct when the
    model changes, instead of a hand-written literal that silently rots.
    """
    if isinstance(base, type) and issubclass(base, BaseModel):
        item = {
            name: _JSON_PLACEHOLDERS.get(_unwrap(info.annotation), "value")
            for name, info in base.model_fields.items()
        }
    else:
        item = {"field": "value"}

    return json.dumps([item], ensure_ascii=False, separators=(",", ":"))


def _schema_for_spec(spec: FilterSpec) -> Schema:
    if spec.lookup == FilterLookupEnum.JSON:
        # Query params are strings; the value is JSON *inside* that string, so
        # documenting it as an array would tell clients to send `?x[]=...`.
        description = (
            f"JSON array of `{getattr(spec.base_type, '__name__', spec.base_type)}` "
            f"objects, URL-encoded."
        )
        if spec.max_length is not None:
            description += f" At most {spec.max_length} items."

        return Schema(
            type=OpenAPIType.STRING,
            examples=[_json_example(spec.base_type)],
            description=description,
        )

    if spec.lookup == FilterLookupEnum.RANGE:
        if spec.base_type in (Decimal, float):
            examples = ["1500.10,3540.53", "34.98,41.40"]
        elif spec.base_type is int:
            examples = ["13,20", "50,1000"]
        elif spec.base_type is datetime:
            examples = ["2020-01-10T10:24:59,2024-03-15T21:23:59"]
        elif spec.base_type is date:
            examples = ["2020-01-10,2026-07-10"]
        else:
            examples = ["<start>,<end>"]

        return Schema(
            type=OpenAPIType.STRING,
            examples=examples,
        )

    base = spec.base_type

    if (
        isinstance(base, type)
        and issubclass(base, Enum)
        and spec.lookup != FilterLookupEnum.IN
    ):
        return _enum_schema(base)

    otype, fmt = _PY_TO_OPENAPI.get(base, (OpenAPIType.STRING, None))
    schema = Schema(type=otype, format=fmt)

    if spec.base_type is bool:
        examples = ["true", "false"]

    if spec.gt is not None:
        schema.exclusive_minimum = _to_number(spec.gt)
    if spec.gte is not None:
        schema.minimum = _to_number(spec.gte)
    if spec.lt is not None:
        schema.exclusive_maximum = _to_number(spec.lt)
    if spec.lte is not None:
        schema.maximum = _to_number(spec.lte)
    if spec.min_length is not None:
        schema.min_length = spec.min_length
    if spec.max_length is not None:
        schema.max_length = spec.max_length
    if spec.choices is not None:
        if spec.lookup is not FilterLookupEnum.IN:
            schema.enum = [
                c.value if isinstance(c, Enum) else _to_number(c) for c in spec.choices
            ]
        else:
            schema.description = (schema.description or "") + (
                f"\nAvailable choices: {', '.join(str(_item) for _item in spec.choices)}"
            )

    return schema


def _schema_for_plain(annotation: Any) -> Schema:
    base = _unwrap(annotation)
    if isinstance(base, type) and issubclass(base, Enum):
        return _enum_schema(base)
    otype, fmt = _PY_TO_OPENAPI.get(base, (OpenAPIType.STRING, None))
    return Schema(type=otype, format=fmt)


def _param_for_ordering(model: type[OrderingQueryMixin]) -> Parameter:
    description = (
        "comma separated fields for ordering. char `-` in beginning of field for setting "
        f"direction to `desc`. otherwise, to `asc`. **Allowed fields**: {', '.join(model.get_allowed_fields())}"
    )

    return Parameter(
        name="ordering",
        param_in="query",
        style="query",  # FORM from OpenAPI spec
        schema=Schema(
            title="ordering",
            type=OpenAPIType.STRING,
            examples=["-created_at", "-created_at,name", "name,-created_at"],
            description=description,
        ),
        description=description,
        required=False,
        explode=False,
        example="-created_at,name",
    )


def _build_query_parameters(
    model: type[BaseModel], exclude: AbstractSet[str] = frozenset()
) -> List[Parameter]:
    """Turn a FilterMeta query model's fields into OpenAPI query parameters.

    The attribute name is the query-param name; filter fields draw their schema
    from the resolved FilterSpec (bounds / enum / choices / description), plain
    fields (search, limit, offset) from their annotation.

    ``exclude`` carries the route's path-parameter names: those fields reach the
    model from the URL (see `path_bound_query`), so documenting them as query
    params would both invite a bogus value and mask Litestar's own path entry.
    """
    params: List[Parameter] = []

    if issubclass(model, OrderingQueryMixin):
        _param = _param_for_ordering(model)

        if _param is not None:
            params.append(_param)

    for name, info in model.model_fields.items():
        if name == "ordering" and issubclass(model, OrderingQueryMixin):
            continue

        if name in exclude:
            continue

        spec = PydanticFilterParser.extract_spec(info.metadata)

        # A structured field normally has no query-string form, so it is left
        # undocumented. A `FilterSpec.json` field is the exception: it is
        # structured *and* query-sendable, because it travels as a JSON-encoded
        # string that the pipeline decodes (`_parse_json`).
        if _is_structured(info.annotation) and (
            spec is None or spec.lookup is not FilterLookupEnum.JSON
        ):
            continue

        if spec is not None:
            schema = _schema_for_spec(spec)
            description = spec.description
        else:
            schema = _schema_for_plain(info.annotation)
            description = info.description

        params.append(
            Parameter(
                name=name,
                param_in="query",
                required=info.is_required(),
                schema=schema,
                description=description,
            )
        )

    return params


Q = TypeVar("Q", bound=BaseModel)

#: Handler parameter name bound by `path_bound_query`. Deliberately not
#: ``query``: Litestar reserves that kwarg for its own query-string binding -
#: which is exactly what plain `query: SomeListQuery` handlers rely on - and
#: refuses to let a dependency shadow it.
QUERY_DEPENDENCY_KEY = "list_query"


def path_bound_query(model: Type[Q]) -> dict[str, Provide]:
    """Bind a query model whose fields span the query string, body *and* URL path.

    Litestar's reserved ``query`` kwarg builds the model out of the query string
    alone, so a model carrying a path-sourced field - ``DocumentEntryListQuery.
    subject_id``, ``SubjectStockProductsListQuery.id`` - would fail validation
    with that field ``missing``. Merging the other sources in keeps such handlers
    down to a single query parameter instead of re-listing every filter by hand.

    Returns the whole ``dependencies`` mapping so the key is never spelled out at
    the call site; the handler takes it as ``list_query: <model>``.

    Sources are applied query -> body -> path, so:

    * the body wins over the query string, because on a ``POST`` the body is the
      request's actual payload and a query param is the incidental one;
    * the path wins over both, because a path parameter is part of the route's
      identity and must not be overridable by the caller.

    A JSON body is merged only for the keys it actually carries, and ``None``
    values in it are ignored: every optional field on a read query already
    defaults to ``None``, so an explicit null adds nothing - while letting it
    through would blank out a value the query string legitimately supplied.
    This is what lets a ``POST`` endpoint take a structured field the query
    string cannot express (``ProductRemainsQuery.char_values``) alongside
    scalars the caller sends as query params.
    """

    async def _dependency(request: Request) -> Q:
        # `dict()` over the MultiDict keeps the first value per key, which is
        # what Litestar's own model binding does with a repeated param.
        raw: dict[str, Any] = dict(request.query_params)

        # GET/DELETE routes simply have no body, so this is a no-op for them.
        # Litestar caches the parsed body, so reading it here does not consume
        # it for anything downstream.
        try:
            body = await request.json()
        except Exception:
            body = None
        if isinstance(body, dict):
            raw.update({k: v for k, v in body.items() if v is not None})

        raw.update(request.path_params)

        try:
            return model.model_validate(raw)
        except ValidationError as exc:
            # Mirror the shape Litestar produces when it binds the model itself,
            # so both styles of handler fail the same way for a client.
            raise ValidationException(
                detail=f"Validation failed for {request.method} {request.url}",
                extra=[
                    {
                        "key": ".".join(str(p) for p in err["loc"]) or "detail",
                        "message": err["msg"],
                    }
                    for err in exc.errors(include_url=False)
                ],
            ) from exc

    return {QUERY_DEPENDENCY_KEY: Provide(_dependency)}


def _should_parse_query_openapi_docs(model: Type[BaseModel]) -> bool:
    return issubclass(model, (FilterMeta, Query, OrderingQueryMixin))


def _find_query_model(handler: HTTPRouteHandler) -> Type[BaseModel] | None:
    signature = handler.parsed_fn_signature

    if signature is None:
        return None

    for typdef in signature.parameters.values():
        annotation = typdef.annotation

        if not (isinstance(annotation, type) and issubclass(annotation, BaseModel)):
            continue

        if _should_parse_query_openapi_docs(annotation):
            return annotation

    return None


def inject_filter_parameters(app: Litestar) -> None:
    schema = app.openapi_schema  # accessing it forces the build + caches it
    paths = schema.paths or {}

    for route in app.routes:
        if not isinstance(route, HTTPRoute):
            continue

        path_item = paths.get(route.path_format)
        if path_item is None:
            continue

        for handler in route.route_handlers:
            model = _find_query_model(handler)
            if model is None:
                continue

            params = _build_query_parameters(model, exclude=set(route.path_parameters))
            new_names = {p.name for p in params}

            for method in handler.http_methods:  # {"GET"} etc.
                operation = getattr(path_item, method.lower(), None)
                if operation is None:
                    continue
                # Drop any opaque/placeholder param Litestar emitted for the
                # model itself, then add the exploded per-field params.
                kept = [
                    p for p in (operation.parameters or []) if p.name not in new_names
                ]
                operation.parameters = kept + params
