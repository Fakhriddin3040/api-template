from typing import Protocol


class OTPGenerator(Protocol):
    def __call__(self) -> str: ...
