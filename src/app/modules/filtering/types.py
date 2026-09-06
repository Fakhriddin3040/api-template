from dataclasses import dataclass
import datetime as datetime_package
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Tuple, Type

from src.app.shared_kernel.types.base_types import Numeric
from src.app.modules.filtering.enums import FilterLookupEnum
from src.app.shared_kernel.utils.functions.common_funcs import tuple_from_enum

_SCALAR_ALLOWED_LOOKUPS = (
    FilterLookupEnum.EQ,
    FilterLookupEnum.GT,
    FilterLookupEnum.LT,
    FilterLookupEnum.GTE,
    FilterLookupEnum.LTE,
)

_COLLECTION_ALLOWED_LOOKUPS = (FilterLookupEnum.IN,)

type ChoicesInT[T] = Tuple[T, ...] | Type[Enum]


def _to_decimal(value: Optional[Numeric]) -> Optional[Decimal]:
    return Decimal(value) if value is not None else None


class FilterContainer[TValue]:
    """Result of a validated + accepted filter, handed to the compiler."""

    __slots__ = ("value", "lookup", "field")

    def __init__(self, value: TValue, lookup: FilterLookupEnum, field: str) -> None:
        self.value = value
        self.lookup = lookup
        self.field = field


@dataclass(frozen=True, slots=True)
class FilterSpec[TValue]:
    """
    Pure declarative specification of a filter field. Holds no behavior.

    A spec describes *what* a field is (its `base_type`, `lookup`, presence
    rules and constraints); it does not convert, validate or serialize. The
    upstream Pydantic layer coerces raw input to `base_type`; `FilterValidator`
    reads the declared props to validate; a compiler turns accepted values into
    a `FilterContainer`.

    Not every prop is meaningful for every field. Use the classmethod factories
    (`FilterSpec.numeric`, `FilterSpec.date_range`, ...) to build well-formed
    specs instead of the raw constructor.
    """

    base_type: Type[TValue]
    lookup: FilterLookupEnum = FilterLookupEnum.EQ
    field: Optional[str] = None
    required: bool = False
    # Range (BETWEEN) only: both endpoints must be present.
    both_required: bool = False
    # Comparable bounds (numeric / date / datetime).
    gt: Optional[Any] = None
    gte: Optional[Any] = None
    lt: Optional[Any] = None
    lte: Optional[Any] = None
    # String only.
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    # Membership: value (or each range endpoint) must be one of these.
    choices: Optional[Tuple[TValue, ...]] = None
    # OpenAPI metadata; ignored by validation.
    description: Optional[str] = None

    # For collections to consider unique constraints
    unique: bool = True

    @staticmethod
    def _ensure_scalar_lookup(lookup: FilterLookupEnum) -> None:
        if lookup not in _SCALAR_ALLOWED_LOOKUPS:
            raise ValueError(
                f"Lookup {lookup} is not a scalar lookup; "
                f"allowed: {_SCALAR_ALLOWED_LOOKUPS}"
            )

    @staticmethod
    def _parse_choices(
        choices: Optional[Tuple[Any, ...] | Type[Enum]],
    ) -> Optional[Tuple[Any, ...]]:
        if choices is None:
            return None

        elif isinstance(choices, type) and issubclass(choices, Enum):
            return tuple_from_enum(choices)
        else:
            return tuple(_to_decimal(c) for c in choices)

    # --- scalar factories -------------------------------------------------

    @classmethod
    def numeric(
        cls,
        base_type: Type[Numeric],
        field: Optional[str] = None,
        lookup: FilterLookupEnum = FilterLookupEnum.EQ,
        required: bool = False,
        gt: Optional[Numeric] = None,
        gte: Optional[Numeric] = None,
        lt: Optional[Numeric] = None,
        lte: Optional[Numeric] = None,
        choices: Optional[ChoicesInT[Numeric]] = None,
        description: Optional[str] = None,
    ) -> "FilterSpec[Numeric]":
        cls._ensure_scalar_lookup(lookup)

        return cls(
            base_type=base_type,
            lookup=lookup,
            field=field,
            required=required,
            gt=_to_decimal(gt),
            gte=_to_decimal(gte),
            lt=_to_decimal(lt),
            lte=_to_decimal(lte),
            choices=cls._parse_choices(choices),
            description=description,
        )

    @classmethod
    def date(
        cls,
        field: Optional[str] = None,
        lookup: FilterLookupEnum = FilterLookupEnum.EQ,
        required: bool = False,
        gt: Optional[datetime_package.date] = None,
        gte: Optional[datetime_package.date] = None,
        lt: Optional[datetime_package.date] = None,
        lte: Optional[datetime_package.date] = None,
        description: Optional[str] = None,
    ) -> "FilterSpec[datetime_package.date]":
        cls._ensure_scalar_lookup(lookup)
        return cls(
            base_type=datetime_package.date,
            lookup=lookup,
            field=field,
            required=required,
            gt=gt,
            gte=gte,
            lt=lt,
            lte=lte,
            description=description,
        )

    @classmethod
    def datetime(
        cls,
        field: Optional[str] = None,
        lookup: FilterLookupEnum = FilterLookupEnum.EQ,
        required: bool = False,
        gt: Optional[datetime_package.datetime] = None,
        gte: Optional[datetime_package.datetime] = None,
        lt: Optional[datetime_package.datetime] = None,
        lte: Optional[datetime_package.datetime] = None,
        description: Optional[str] = None,
    ) -> "FilterSpec[datetime_package.datetime]":
        cls._ensure_scalar_lookup(lookup)
        return cls(
            base_type=datetime_package.datetime,
            lookup=lookup,
            field=field,
            required=required,
            gt=gt,
            gte=gte,
            lt=lt,
            lte=lte,
            description=description,
        )

    @classmethod
    def string(
        cls,
        field: Optional[str] = None,
        required: bool = False,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        choices: Optional[ChoicesInT[str]] = None,
        description: Optional[str] = None,
    ) -> "FilterSpec[str]":
        return cls(
            base_type=str,
            lookup=FilterLookupEnum.EQ,
            field=field,
            required=required,
            min_length=min_length,
            max_length=max_length,
            choices=cls._parse_choices(choices),
            description=description,
        )

    @classmethod
    def enum[TEnum: Enum](
        cls,
        enum_type: Type[TEnum],
        field: Optional[str] = None,
        required: bool = False,
        choices: Optional[ChoicesInT[TEnum]] = None,
        description: Optional[str] = None,
    ) -> "FilterSpec[TEnum]":
        """
        Enum-typed filter. `base_type` is the enum, so Pydantic coerces raw
        input to a member and rejects unknowns. `choices` narrows the accepted
        members further (defaults to the whole enum).
        """
        return cls(
            base_type=enum_type,
            lookup=FilterLookupEnum.EQ,
            field=field,
            required=required,
            choices=(
                cls._parse_choices(choices) if choices else tuple_from_enum(enum_type)
            ),
            description=description,
        )

    # --- range factories --------------------------------------------------

    @classmethod
    def numeric_range(
        cls,
        base_type: Type[Numeric],
        field: Optional[str] = None,
        required: bool = False,
        both_required: bool = False,
        gt: Optional[Numeric] = None,
        gte: Optional[Numeric] = None,
        lt: Optional[Numeric] = None,
        lte: Optional[Numeric] = None,
        description: Optional[str] = None,
    ) -> "FilterSpec[Numeric]":
        return cls(
            base_type=base_type,
            lookup=FilterLookupEnum.RANGE,
            field=field,
            required=required or both_required,
            both_required=both_required,
            gt=_to_decimal(gt),
            gte=_to_decimal(gte),
            lt=_to_decimal(lt),
            lte=_to_decimal(lte),
            description=description,
        )

    @classmethod
    def date_range(
        cls,
        field: Optional[str] = None,
        required: bool = False,
        both_required: bool = False,
        gt: Optional[datetime_package.date] = None,
        gte: Optional[datetime_package.date] = None,
        lt: Optional[datetime_package.date] = None,
        lte: Optional[datetime_package.date] = None,
        description: Optional[str] = None,
    ) -> "FilterSpec[datetime_package.date]":
        return cls(
            base_type=datetime_package.date,
            lookup=FilterLookupEnum.RANGE,
            field=field,
            required=required or both_required,
            both_required=both_required,
            gt=gt,
            gte=gte,
            lt=lt,
            lte=lte,
            description=description,
        )

    @classmethod
    def datetime_range(
        cls,
        field: Optional[str] = None,
        required: bool = False,
        both_required: bool = False,
        gt: Optional[datetime_package.datetime] = None,
        gte: Optional[datetime_package.datetime] = None,
        lt: Optional[datetime_package.datetime] = None,
        lte: Optional[datetime_package.datetime] = None,
        description: Optional[str] = None,
    ) -> "FilterSpec[datetime_package.datetime]":
        return cls(
            base_type=datetime_package.datetime,
            lookup=FilterLookupEnum.RANGE,
            field=field,
            required=required or both_required,
            both_required=both_required,
            gt=gt,
            gte=gte,
            lt=lt,
            lte=lte,
            description=description,
        )

    @classmethod
    def boolean(
        cls,
        required: bool = False,
        description: Optional[str] = None,
    ) -> "FilterSpec[bool]":
        return cls(
            base_type=bool,
            required=required,
            lookup=FilterLookupEnum.EQ,
            choices=("true", "false"),
            description=description,
        )

    @classmethod
    def json(
        cls,
        base_type: Type[TValue],
        field: Optional[str] = None,
        required: bool = False,
        max_length: Optional[int] = None,
        description: Optional[str] = None,
    ) -> "FilterSpec[Tuple[TValue, ...]]":
        """A structujsonred filter whose value arrives as JSON rather than a scalar.

        `base_type` is the item model (a pydantic model or msgspec struct); the
        value is always a list of it, so a single-item payload is still sent as
        a JSON array. `max_length` caps how many items are accepted.

        The payload's *meaning* is the compiler's business: a `json` filter has
        no generic column path, so it must have a
        `compile_<field>__json` handler.
        """
        return cls(
            base_type=base_type,
            lookup=FilterLookupEnum.JSON,
            field=field,
            required=required,
            max_length=max_length,
            description=description,
        )

    @classmethod
    def collection(
        cls,
        base_type: Type[TValue],
        lookup: FilterLookupEnum,
        required: bool = False,
        description: Optional[str] = None,
        choices: Optional[ChoicesInT] = None,
        unique: bool = True,
    ) -> "FilterSpec[Tuple[TValue, ...]]":
        if lookup not in _COLLECTION_ALLOWED_LOOKUPS:
            raise RuntimeError("Invalid lookup for collection filter")

        if choices:
            _choices = cls._parse_choices(choices)
        if isinstance(base_type, Enum):
            _choices = tuple_from_enum(base_type)
        else:
            _choices = None

        return cls(
            base_type=base_type,
            lookup=lookup,
            required=required,
            description=description,
            choices=_choices,
            unique=unique,
        )


# Declared types
type FilterSpecCollection = Tuple[FilterSpec, ...]
type FilterContainerCollection = Tuple[FilterContainer, ...]
