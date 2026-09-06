from abc import ABC
from dataclasses import asdict
from typing import Optional, List, ClassVar

from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.ports.result import Result
from src.app.shared_kernel.types.base_types import ListLike
from src.app.shared_kernel.validation.value_validation.value_validation_schema import (
    ValueValidationProfile,
)


class DomainInputParams(ABC):  # noqa: B024 - ABC marks intent; subclasses add fields, not methods
    value_validation_profile: ClassVar[Optional[ValueValidationProfile]] = None
    _is_base: bool = False

    def validate(
        self, field_prefix: str = ""
    ) -> Result[None, List[AppExceptionDetail]]:
        errs = []

        for k, v in self.__dict__.items():
            if not v:
                continue

            if isinstance(v, DomainInputParams):
                if (
                    not hasattr(v, "value_validation_profile")
                    or not v.value_validation_profile
                ):
                    continue

                res = v.validate(field_prefix=k)
                if res.is_err():
                    errs.extend(res.unwrap_err())

            elif not isinstance(v, str) and isinstance(v, ListLike):
                for i in range(len(v)):
                    if isinstance(v[i], DomainInputParams):

                        if (
                            not hasattr(v[i], "value_validation_profile")
                            or not v[i].value_validation_profile
                        ):
                            break

                        res = v[i].validate(
                            field_prefix=f"{field_prefix + '.' if field_prefix else ''}{k}[{i}]"
                        )
                        if res.is_err():
                            errs.extend(res.unwrap_err())

        if hasattr(self, "value_validation_profile") and self.value_validation_profile:
            results = self.value_validation_profile.validate(src=self)

            if results.is_err():
                errs.extend(results.unwrap_err())

        if not errs:
            return Result.OK

        self._rename_exc_fields(field_prefix, errs)
        return Result.err(errs)

    def _rename_exc_fields(
        self, field_prefix: str, errs: List[AppExceptionDetail]
    ) -> None:
        if not field_prefix:
            return

        for err in errs:
            err.field = f"{field_prefix}.{err.field}"

    # def __new__(cls, *args, **kwargs):
    #     if (
    #         not cls != DomainInputParams
    #         and hasattr(cls, "value_validation_profile")
    #         or (
    #             not getattr(cls, "_is_base")
    #             and not getattr(cls, "value_validation_profile")
    #         )
    #     ):
    #         raise ValueError("Value validation profile not defined in ", str(cls))
    #     return super().__new__(cls)

    def as_dict(self):
        return asdict(self)
