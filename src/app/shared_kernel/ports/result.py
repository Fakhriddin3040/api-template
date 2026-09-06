from __future__ import annotations
from dataclasses import dataclass
from typing import (
    Callable,
    Generic,
    TypeVar,
    Union,
    TypeAlias,
    Any,
    Iterable,
    Sequence,
    List,
)

from src.app.shared_kernel.types.base_types import ListLike
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail, AppException
from src.app.shared_kernel.errors.constants import (
    AppExceptionStatusCodes,
    AppExceptionMessage,
)

TValue = TypeVar("TValue")
TError = TypeVar("TError")
U = TypeVar("U")
F = TypeVar("F")


@dataclass(frozen=True)
class Ok(Generic[TValue]):
    value: TValue


@dataclass(frozen=True)
class Err(Generic[TError]):
    error: TError


class Result(Generic[TValue, TError]):
    __slots__ = ("_inner",)

    OK: Result[Any, Any]

    def __init__(self, inner: Union[Ok[TValue], Err[TError]]):
        self._inner = inner

    @classmethod
    def ok(cls, value: TValue) -> "Result[TValue, TError]":
        return cls(Ok(value))

    @classmethod
    def err(cls, error: TError) -> "Result[TValue, TError]":
        return cls(Err(error))

    def is_ok(self) -> bool:
        return isinstance(self._inner, Ok)

    def is_err(self) -> bool:
        return isinstance(self._inner, Err)

    def unwrap(self) -> TValue:
        if isinstance(self._inner, Ok):
            return self._inner.value
        raise RuntimeError(f"called unwrap() on Err: {self._inner}")

    def unwrap_or(self, default: TValue) -> TValue:
        return self._inner.value if isinstance(self._inner, Ok) else default

    def unwrap_err(self) -> TError:
        if isinstance(self._inner, Err):
            return self._inner.error
        raise RuntimeError(f"called unwrap_err() on Ok: {self._inner}")

    def unwrap_anyway(self) -> Union[TValue, TError]:
        if self.is_ok():
            return self.unwrap()
        return self.unwrap_err()

    def map(self, fn: Callable[[TValue], U]) -> "Result[U, TError]":
        if isinstance(self._inner, Ok):
            return Result.ok(fn(self._inner.value))
        return Result(self._inner)

    def map_err(self, fn: Callable[[TError], F]) -> "Result[TValue, F]":
        if isinstance(self._inner, Err):
            return Result.err(fn(self._inner.error))
        return Result(self._inner)

    def as_app_exception(self) -> AppException:
        if not self.is_err():
            raise ValueError(f"called to_exception() on Ok: {self._inner}")

        return AppException(
            details=self.unwrap_err(),
            exception_status=AppExceptionStatusCodes.DETAILED_ERROR,
            message=AppExceptionMessage.DETAILED_ERROR,
        )

    @classmethod
    def merge_errs(
        cls, results: Iterable[Result[Any, TError]]
    ) -> Result[Any, Union[TError, List[TError]]]:
        errs: List[TError] = []

        for res in results:
            if res.is_err():
                err = res.unwrap_err()
                if isinstance(err, Sequence):
                    errs.extend(err)
                else:
                    errs.append(err)

        if not errs:
            return Result.ok(None)

        return Result.err(errs)

    @classmethod
    def from_errs(
        cls, errs: ListLike[AppExceptionDetail]
    ) -> Result[Any, List[AppExceptionDetail]]:
        if errs:
            return cls.err(errs)
        return cls.OK


ResultErrDetailed: TypeAlias = Result[None, AppExceptionDetail]
ResultErr = Result[None, AppException]

Result.OK = Result.ok(None)


type ResultDetailed[TValue] = Result[TValue, List[AppExceptionDetail]]
