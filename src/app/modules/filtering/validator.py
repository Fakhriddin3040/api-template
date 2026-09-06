from enum import Enum
from typing import Any, List, Optional, Tuple, Iterable

from src.app.shared_kernel.errors.app_exception import (
    AppException,
    AppExceptionDetail,
)
from src.app.shared_kernel.errors.constants import (
    AppExceptionMessage,
    AppExceptionStatusCodes,
    AppExceptionDetailPayloadKeys,
    AppExceptionLocationEnum,
)
from src.app.modules.filtering.enums import FilterLookupEnum
from src.app.modules.filtering.types import FilterSpec


class FilterValidator:
    """
    Stateless validator for `FilterSpec`.

    Values before validation must exact to `FilterSpec.base_type`
    """

    @classmethod
    def validate(cls, spec: FilterSpec, value: Optional[Any]) -> None:
        if spec.field is None:
            raise RuntimeError("FilterSpec.field must be set before validation")

        elif spec.lookup == FilterLookupEnum.EQ:
            cls._validate_scalar(spec, value)

        elif spec.lookup == FilterLookupEnum.RANGE:
            cls._validate_range(spec, value)

        elif spec.lookup == FilterLookupEnum.IN:
            cls._validate_collection(spec, value)

        elif spec.lookup == FilterLookupEnum.JSON:
            cls._validate_json(spec, value)

        else:
            raise RuntimeError(f"Undefined filter lookup type `{spec.lookup}`")

    @classmethod
    def _validate_scalar(cls, spec: FilterSpec, value: Optional[Any]) -> None:
        if value is None:
            if spec.required:
                raise AppException.from_details([cls._required_detail(spec)])
            return

        details = cls._validate_bounds(spec, value)
        details.extend(cls._validate_length(spec, value))
        details.extend(cls._validate_choices(spec, value))

        if details:
            raise AppException.from_details(details)

    @classmethod
    def _validate_range(cls, spec: FilterSpec, value: Optional[Any]) -> None:
        if value is None:
            if spec.required:
                raise AppException.from_details([cls._required_detail(spec)])
            return

        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise AppException.from_details([cls._invalid_value_detail(spec)])

        low, high = value

        if low is None and high is None:
            raise ValueError(
                "Range filter requires at least one boundary. "
                "Use 'value,' for lower bound or ',value' for upper bound."
            )

        if (low is None or high is None) and spec.both_required:
            raise AppException.from_details([cls._required_detail(spec)])

        details: List[AppExceptionDetail] = []

        if low is not None and high is not None and low > high:
            details.append(cls._range_order_detail(spec, low, high))

        for endpoint in (low, high):
            if endpoint is not None:
                details.extend(cls._validate_bounds(spec, endpoint))
                details.extend(cls._validate_choices(spec, endpoint))

        if details:
            raise AppException.from_details(details)

    @classmethod
    def _validate_collection(
        cls, spec: FilterSpec, value: Optional[Tuple[Any, ...]]
    ) -> None:
        if value is not None and not isinstance(value, (tuple, list)):
            raise AppException.from_details([cls._invalid_value_detail(spec)])

        if value is None or all(v is None for v in value):
            if spec.required:
                raise AppException.from_details([cls._required_detail(spec)])
            return

        if any(v is None for v in value):
            raise AppException.from_details([cls._invalid_value_detail(spec)])

        if any(not isinstance(v, spec.base_type) for v in value):
            raise AppException.from_details([cls._invalid_value_detail(spec)])

        details: List[AppExceptionDetail] = []

        duplicates = set()
        seen = set()

        for endpoint in value:
            details.extend(cls._validate_bounds(spec, endpoint))
            details.extend(cls._validate_choices(spec, endpoint))

            if endpoint in seen:
                duplicates.add(endpoint)
            else:
                seen.add(endpoint)

        if duplicates:
            details.append(cls._duplicate_detail(spec, duplicates))

        if details:
            raise AppException.from_details(details)

    @classmethod
    def _validate_json(cls, spec: FilterSpec, value: Optional[Any]) -> None:
        """The item schema is enforced by pydantic before this runs, so only
        presence and item count are checked here."""
        if value is None or (isinstance(value, (tuple, list)) and not value):
            if spec.required:
                raise AppException.from_details([cls._required_detail(spec)])
            return

        if not isinstance(value, (tuple, list)):
            raise AppException.from_details([cls._invalid_value_detail(spec)])

        details = cls._validate_length(spec, value)

        if details:
            raise AppException.from_details(details)

    # --- constraint checks ------------------------------------------------

    @classmethod
    def _validate_bounds(cls, spec: FilterSpec, value: Any) -> List[AppExceptionDetail]:
        details: List[AppExceptionDetail] = []

        if spec.gt is not None and not value > spec.gt:
            details.append(cls._bound_detail(spec, "gt"))
        if spec.gte is not None and not value >= spec.gte:
            details.append(cls._bound_detail(spec, "gte"))
        if spec.lt is not None and not value < spec.lt:
            details.append(cls._bound_detail(spec, "lt"))
        if spec.lte is not None and not value <= spec.lte:
            details.append(cls._bound_detail(spec, "lte"))

        return details

    @classmethod
    def _validate_length(cls, spec: FilterSpec, value: Any) -> List[AppExceptionDetail]:
        if spec.min_length is None and spec.max_length is None:
            return []

        length = len(value)

        if (spec.min_length is not None and length < spec.min_length) or (
            spec.max_length is not None and length > spec.max_length
        ):
            return [cls._length_detail(spec)]

        return []

    @classmethod
    def _validate_choices(
        cls, spec: FilterSpec, value: Any
    ) -> List[AppExceptionDetail]:
        if spec.choices is None or value in spec.choices:
            return []

        return [cls._choices_detail(spec)]

    # --- detail builders --------------------------------------------------

    @staticmethod
    def _required_detail(spec: FilterSpec) -> AppExceptionDetail:
        return AppExceptionDetail(
            status=AppExceptionStatusCodes.REQUIRED_FILTER,
            message=AppExceptionMessage.REQUIRED_VALUE,
            field=spec.field,
            payload={
                AppExceptionDetailPayloadKeys.LOOKUP: spec.lookup,
                AppExceptionDetailPayloadKeys.LOCATION: AppExceptionLocationEnum.QUERY_PARAMS,
            },
        )

    @staticmethod
    def _invalid_value_detail(spec: FilterSpec) -> AppExceptionDetail:
        return AppExceptionDetail(
            status=AppExceptionStatusCodes.INVALID_VALUE,
            message=AppExceptionMessage.INVALID_VALUE,
            field=spec.field,
            payload={
                AppExceptionDetailPayloadKeys.LOCATION: AppExceptionLocationEnum.QUERY_PARAMS,
            },
        )

    @staticmethod
    def _bound_detail(spec: FilterSpec, bound: str) -> AppExceptionDetail:
        return AppExceptionDetail(
            status=AppExceptionStatusCodes.INVALID_VALUE,
            message=AppExceptionMessage.INVALID_VALUE,
            field=spec.field,
            payload={
                AppExceptionDetailPayloadKeys.RANGES: {bound: getattr(spec, bound)}
            },
        )

    @staticmethod
    def _range_order_detail(
        spec: FilterSpec, low: Any, high: Any
    ) -> AppExceptionDetail:
        return AppExceptionDetail(
            status=AppExceptionStatusCodes.INVALID_VALUE,
            message=AppExceptionMessage.INVALID_VALUE,
            field=spec.field,
            payload={
                AppExceptionDetailPayloadKeys.RANGES: {"low": low, "high": high},
            },
        )

    @staticmethod
    def _length_detail(spec: FilterSpec) -> AppExceptionDetail:
        return AppExceptionDetail(
            status=AppExceptionStatusCodes.INVALID_VALUE,
            message=AppExceptionMessage.INVALID_VALUE,
            field=spec.field,
            payload={
                AppExceptionDetailPayloadKeys.LOCATION: AppExceptionLocationEnum.QUERY_PARAMS,
                AppExceptionDetailPayloadKeys.RANGES: {
                    "min_length": spec.min_length,
                    "max_length": spec.max_length,
                },
            },
        )

    @staticmethod
    def _choices_detail(spec: FilterSpec) -> AppExceptionDetail:
        return AppExceptionDetail(
            status=AppExceptionStatusCodes.INVALID_VALUE,
            message=AppExceptionMessage.INVALID_VALUE,
            field=spec.field,
            payload={
                AppExceptionDetailPayloadKeys.LOCATION: AppExceptionLocationEnum.QUERY_PARAMS,
                AppExceptionDetailPayloadKeys.VALUES: [
                    c.value if isinstance(c, Enum) else c for c in spec.choices
                ],
            },
        )

    @staticmethod
    def _duplicate_detail(
        spec: FilterSpec, duplicates: Iterable[Any]
    ) -> AppExceptionDetail:
        return AppExceptionDetail(
            status=AppExceptionStatusCodes.DUPLICATED,
            message=AppExceptionMessage.DUPLICATED_FILTER_VALUE,
            field=spec.field,
            payload={
                AppExceptionDetailPayloadKeys.LOCATION: AppExceptionLocationEnum.QUERY_PARAMS,
                AppExceptionDetailPayloadKeys.VALUES: duplicates,
            },
        )
