from __future__ import annotations

from decimal import Decimal

import regex
from typing import TypeAlias, Union, Protocol, Any, Optional, List, TYPE_CHECKING

from src.app.shared_kernel.constants import error_message_const as err_msg
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import (
    AppExceptionStatusCodes,
    AppExceptionDetailPayloadKeys,
)
from src.app.shared_kernel.ports.result import Result
from src.app.shared_kernel.types.base_types import ListLike

if TYPE_CHECKING:
    from src.app.shared_kernel.validation.value_validation.value_validation_schema import (
        FieldValueValidationSpec,
    )


Numeric: TypeAlias = Union[int, float, Decimal]


class ValueValidator(Protocol):
    def __call__(
        self, field: str, v: Any
    ) -> Result[None, AppExceptionDetail | List[AppExceptionDetail]]: ...


def _err(
    message: str,
    field: str,
    status: AppExceptionStatusCodes,
    critical: bool = False,
    payload: Optional[dict] = None,
) -> Result[None, AppExceptionDetail]:
    return Result.err(
        AppExceptionDetail(
            message=message,
            field=field,
            payload=payload or {},
            status=status,
            critical=critical,
        )
    )


def _err_list(
    message: str,
    field: str,
    status: AppExceptionStatusCodes,
    critical: bool = False,
    payload: Optional[dict] = None,
) -> Result[None, List[AppExceptionDetail]]:
    return Result.err(
        [
            AppExceptionDetail(
                message=message,
                field=field,
                payload=payload or {},
                status=status,
                critical=critical,
            )
        ]
    )


def _ok() -> Result[None, AppExceptionDetail]:
    return Result.ok(None)


def _ranges(
    *,
    gt: Optional[Numeric] = None,
    gte: Optional[Numeric] = None,
    lt: Optional[Numeric] = None,
    lte: Optional[Numeric] = None,
) -> dict:
    """Build a ``ranges`` payload entry the same way it is emitted elsewhere in
    the project (e.g. ``{"gte": ..., "lte": ...}``), skipping unset bounds."""
    ranges: dict = {}
    if gt is not None:
        ranges["gt"] = gt
    if gte is not None:
        ranges["gte"] = gte
    if lt is not None:
        ranges["lt"] = lt
    if lte is not None:
        ranges["lte"] = lte
    return ranges


# ===== STR =====
def str_required(field: str, v: str) -> Result[None, AppExceptionDetail]:
    if v is None:
        return _err(
            message=err_msg.REQUIRED_VALUE_ERR,
            field=field,
            status=AppExceptionStatusCodes.REQUIRED_VALUE,
            critical=True,
        )
    elif not isinstance(v, str):
        return _err(
            message=err_msg.INVALID_TYPE_ERR,
            field=field,
            status=AppExceptionStatusCodes.INVALID_TYPE,
            critical=True,
        )
    return _ok()


def str_regex(
    field: str, v: str, pattern: regex.Pattern
) -> Result[None, AppExceptionDetail]:
    if v and not pattern.match(v):
        return _err(
            message=err_msg.INVALID_TYPE_ERR,
            field=field,
            status=AppExceptionStatusCodes.REGEX_NOT_MATCH,
            payload={
                AppExceptionDetailPayloadKeys.VALUE: v,
                "pattern": pattern.pattern,
            },
        )
    return _ok()


def str_length(
    field: str,
    v: str,
    max_length: Optional[int] = None,
    min_length: Optional[int] = None,
) -> Result[None, AppExceptionDetail]:
    if not v:
        return _ok()

    length = len(v)
    ranges = _ranges(gte=min_length, lte=max_length)

    if min_length is not None and length < min_length:
        return _err(
            message=err_msg.INVALID_LENGTH_ERR,
            field=field,
            status=AppExceptionStatusCodes.STRING_RANGE_LIMIT_EXCEEDED,
            payload={
                AppExceptionDetailPayloadKeys.VALUE: length,
                AppExceptionDetailPayloadKeys.RANGES: ranges,
            },
        )

    if max_length is not None and length > max_length:
        return _err(
            message=err_msg.INVALID_LENGTH_ERR,
            field=field,
            status=AppExceptionStatusCodes.STRING_RANGE_LIMIT_EXCEEDED,
            payload={
                AppExceptionDetailPayloadKeys.VALUE: length,
                AppExceptionDetailPayloadKeys.RANGES: ranges,
            },
        )

    return _ok()


# ===== NUMERIC =====
def numeric_range(
    field: str, v: int | float | Decimal, gte: Optional[Numeric], lte: Optional[Numeric]
) -> Result[None, AppExceptionDetail]:
    ranges = _ranges(gte=gte, lte=lte)

    if gte is not None and v < gte:
        return _err(
            message=err_msg.NUMERIC_RANGE_LIMIT_EXCEEDED,
            field=field,
            status=AppExceptionStatusCodes.NUMERIC_RANGE_LIMIT_EXCEEDED,
            payload={
                AppExceptionDetailPayloadKeys.VALUE: v,
                AppExceptionDetailPayloadKeys.RANGES: ranges,
            },
        )
    if lte is not None and v > lte:
        return _err(
            message=err_msg.NUMERIC_RANGE_LIMIT_EXCEEDED,
            field=field,
            status=AppExceptionStatusCodes.NUMERIC_RANGE_LIMIT_EXCEEDED,
            payload={
                AppExceptionDetailPayloadKeys.VALUE: v,
                AppExceptionDetailPayloadKeys.RANGES: ranges,
            },
        )

    return _ok()


# ===== INT =====
def int_required(field: str, v: int) -> Result[None, AppExceptionDetail]:
    if v is None:
        return _err(
            message=err_msg.REQUIRED_VALUE_ERR,
            field=field,
            status=AppExceptionStatusCodes.REQUIRED_VALUE,
            critical=True,
        )
    if not isinstance(v, int):
        return _err(
            message=err_msg.INVALID_TYPE_ERR,
            field=field,
            status=AppExceptionStatusCodes.INVALID_TYPE,
            critical=True,
        )
    return _ok()


# Decimal
def decimal_required(
    field: str, v: str | int | float
) -> Result[None, AppExceptionDetail]:
    if v is None:
        return _err(
            message=err_msg.REQUIRED_VALUE_ERR,
            field=field,
            status=AppExceptionStatusCodes.REQUIRED_VALUE,
            critical=True,
        )
    if not isinstance(v, Decimal):
        return _err(
            message=err_msg.INVALID_TYPE_ERR,
            field=field,
            status=AppExceptionStatusCodes.INVALID_TYPE,
            critical=True,
        )
    return _ok()


# ===== OBJECT =====
def object_required(
    field: str, v: str, instance_of: type
) -> Result[None, AppExceptionDetail]:
    if v is None:
        return _err(
            message=err_msg.REQUIRED_VALUE_ERR,
            field=field,
            status=AppExceptionStatusCodes.REQUIRED_VALUE,
            critical=True,
        )
    if not isinstance(v, instance_of):
        return _err(
            message=err_msg.INVALID_TYPE_ERR,
            field=field,
            status=AppExceptionStatusCodes.INVALID_TYPE,
            critical=True,
        )
    return _ok()


# ===== LIST =====
def collection_required(
    field: str,
    v: ListLike,
    instance_of: type,
    collection_of: type | tuple[type, ...] = (list, tuple, set, frozenset),  # ListLike
    child: FieldValueValidationSpec = None,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
) -> Result[None, List[AppExceptionDetail]]:
    if v is None:
        return _err_list(
            message=err_msg.REQUIRED_VALUE_ERR,
            field=field,
            status=AppExceptionStatusCodes.REQUIRED_VALUE,
            critical=True,
        )
    if not isinstance(v, collection_of):
        return _err_list(
            message=err_msg.INVALID_TYPE_ERR,
            field=field,
            status=AppExceptionStatusCodes.INVALID_TYPE,
            critical=True,
        )

    if min_len is not None and len(v) < min_len:
        return _err_list(
            message=err_msg.LIST_INVALID_LENGTH_ERR,
            field=field,
            status=AppExceptionStatusCodes.LIST_INVALID_RANGE,
            payload={
                AppExceptionDetailPayloadKeys.VALUE: len(v),
                AppExceptionDetailPayloadKeys.RANGES: _ranges(gte=min_len, lte=max_len),
            },
        )
    if max_len is not None and len(v) > max_len:
        return _err_list(
            message=err_msg.LIST_INVALID_LENGTH_ERR,
            field=field,
            status=AppExceptionStatusCodes.LIST_INVALID_RANGE,
            payload={
                AppExceptionDetailPayloadKeys.VALUE: len(v),
                AppExceptionDetailPayloadKeys.RANGES: _ranges(gte=min_len, lte=max_len),
            },
        )

    errs = list()

    for i in range(len(v)):
        if not isinstance(v[i], instance_of):
            errs.append(
                AppExceptionDetail(
                    message=err_msg.INVALID_TYPE_ERR,
                    field=field,
                    status=AppExceptionStatusCodes.INVALID_TYPE,
                    payload={"idx": i},
                )
            )
            continue

        if child is not None:
            _res = child.validate(v[i])

            if _res.is_err():
                err = _res.unwrap_err()

                if not err.payload:
                    err.payload = {}

                err.payload["idx"] = i
                errs.append(err)

    if errs:
        return Result.err(errs)

    return Result.ok(None)
