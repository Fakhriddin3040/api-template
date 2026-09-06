from contextvars import ContextVar, Token

from typing import Generic, TypeVar, Optional, Protocol, runtime_checkable

TValue = TypeVar("TValue")
TToken = TypeVar("TToken")


@runtime_checkable
class ContextRegistryProto(Protocol[TValue, TToken]):
    """
    Registry of context

    Generics:
        TValue: Any type to store.
        TToken: Token type to return after set for later cleaning.
    """

    def set(self, v: TValue) -> TToken: ...
    def get(self, required: Optional[bool] = False) -> Optional[TValue]: ...
    def reset(self, token: TToken) -> None: ...


class ContextVarRegistry(Generic[TValue], ContextRegistryProto[TValue, Token]):
    """One ContextVar behind a small interface.

    Deliberately NOT a Singleton. The shared `Singleton` base keyed instances on
    the class, so a second `ContextVarRegistry(key=...)` returned the first
    instance and `__init__` then overwrote its key and storage — quietly
    repointing every existing holder (notably the DB session registry) at the
    new key. Instantiate one per key at module scope instead.
    """

    def __init__(self, key: str) -> None:
        self.key = key
        self.__storage: ContextVar[TValue | None] = ContextVar(key, default=None)

    def set(self, v: TValue) -> Token:
        return self.__storage.set(v)

    def get(self, required: Optional[bool] = False) -> Optional[TValue]:
        value = self.__storage.get()

        if required and value is None:
            raise ValueError(
                f"Required value was not set in '{self.key}' context var registry."
            )

        return value

    def reset(self, token: Token) -> None:
        self.__storage.reset(token)
