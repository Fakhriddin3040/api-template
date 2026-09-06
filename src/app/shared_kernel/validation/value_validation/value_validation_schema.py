from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, List, Optional, Type, Collection

from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.ports.result import Result
from src.app.shared_kernel.types.base_types import ListLike
from src.app.shared_kernel.validation.value_validation.value_validation_rule import (
    ValueValidator,
    str_required,
    str_regex,
    int_required,
    numeric_range,
    str_length,
    decimal_required,
    Numeric,
    object_required,
    collection_required,
)


def optional(func: Callable) -> ValueValidator:
    def _wrapper(field: str, v: Any) -> Result[None, AppExceptionDetail]:
        if v is None:
            return Result.ok(None)
        return func(field=field, v=v)

    return _wrapper


@dataclass(frozen=True)
class FieldValueValidationSpec:
    field: str
    validators: List[ValueValidator]
    required: bool

    def validate(self, v: Any) -> Result[Any, List[AppExceptionDetail]]:
        if not self.required and v is None:
            return Result.ok(None)

        errs = []

        for validator in self.validators:
            res = validator(field=self.field, v=v)

            if res.is_err():
                err = res.unwrap_err()

                if isinstance(err, AppExceptionDetail):
                    errs.append(err)

                    if err.critical:
                        break
                elif isinstance(err, Collection):
                    errs.extend(err)

        if errs:
            return Result.err(errs)
        return Result.ok(None)


@dataclass(frozen=True)
class ValueValidationProfile:
    fields: List[FieldValueValidationSpec]

    def validate(
        self, src: Any, key: Optional[Callable[[Any, str], Any]] = None
    ) -> Result[None, List[AppExceptionDetail]]:
        _key = key or getattr
        res = []

        for field in self.fields:
            v = _key(src, field.field)

            if not field.required and v is None:
                continue

            _res = field.validate(v=v)

            if _res.is_err():
                res.append(_res)

        return Result.merge_errs(res)


def StrFieldValueValidationSpecFactory(  # noqa
    field: str,
    re_pattern: Optional[str] = None,
    required: bool = True,
    max_length: Optional[int] = None,
    min_length: Optional[int] = None,
) -> FieldValueValidationSpec:
    validators = [str_required]
    if re_pattern:
        validators.append(partial(str_regex, pattern=re_pattern))

    if min_length or max_length:
        validators.append(
            partial(str_length, min_length=min_length, max_length=max_length)
        )

    return FieldValueValidationSpec(
        field=field, validators=validators, required=required
    )


def IntFieldValidationSpecFactory(  # noqa
    field: str,
    required: bool = True,
    lte: Optional[Numeric] = None,
    gte: Optional[Numeric] = None,
) -> FieldValueValidationSpec:
    validators = [
        int_required,
        partial(numeric_range, lte=lte, gte=gte),
    ]
    spec = FieldValueValidationSpec(
        field=field,
        validators=validators,
        required=required,
    )
    return spec


def DecimalFieldValidationSpecFactory(  # noqa
    field: str,
    required: bool = True,
    lte: Optional[Numeric] = None,
    gte: Optional[Numeric] = None,
) -> FieldValueValidationSpec:
    validators = [
        decimal_required,
        partial(numeric_range, lte=lte, gte=gte),
    ]
    return FieldValueValidationSpec(
        field=field,
        validators=validators,
        required=required,
    )


def ObjectFieldValidationSpecFactory(  # noqa
    field: str,
    instance_of: type,
    required: bool = True,
) -> FieldValueValidationSpec:

    validators = [partial(object_required, instance_of=instance_of)]
    return FieldValueValidationSpec(
        field=field,
        validators=validators,
        required=required,
    )


def CollectionFieldValidationSpecFactory(  # noqa
    field: str,
    instance_of: type,
    collection_of: Type[ListLike],
    child: Optional[FieldValueValidationSpec] = None,
    required: bool = True,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
) -> FieldValueValidationSpec:
    func = partial(
        collection_required,
        instance_of=instance_of,
        collection_of=collection_of,
        child=child,
        min_len=min_len,
        max_len=max_len,
    )

    validators = [func]

    return FieldValueValidationSpec(
        field=field, validators=validators, required=required
    )
