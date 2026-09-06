from typing import Protocol


class PasswordGenerator(Protocol):
    def __call__(self) -> str: ...
