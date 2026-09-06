from decimal import Decimal
from typing import Literal, TypeAlias, Callable
from typing import (
    Awaitable,
    Any,
    TypeVar,
    Protocol,
    Union,
    Sequence,
    Set,
)
from uuid import UUID

T = TypeVar("T")

# Every aggregate/entity identifier in the project. UUIDv7 values are generated
# by ``src.app.shared_kernel.utils.functions.uuid_funcs.uuid7`` — time-ordered,
# so they index like a sequence while staying non-enumerable.
type ID_T = UUID

Pipeline: TypeAlias = Callable[
    [Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]
]
type ListLike[T: Any] = Union[Sequence[T], Set[T]]
type Numeric = Union[int, float, Decimal]
type NumericConvertable = Union[int, float, Decimal, str]


class FactoryT(Protocol[T]):
    def __call__(self) -> T | Awaitable[T]: ...


Environment = Literal["production", "development", "testing"]
SlugGenerator: TypeAlias = Callable[[str], str]
