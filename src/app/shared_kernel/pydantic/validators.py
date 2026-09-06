import unicodedata
from typing import Callable, Optional

import regex
from regex import Pattern


def normalize_string(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)

    value = regex.sub(r"[\u200B-\u200D\uFEFF]", "", value)

    return value.strip()


def regex_validator_factory(
    pattern: Pattern[str], *, normalize: bool = True, raise_on_err: bool = True
) -> Callable[[str], Optional[str]]:
    """Raises on error or returns None"""

    def _validator(value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("Value must be a string")

        if normalize:
            value = normalize_string(value)

        if not pattern.fullmatch(value):
            if not raise_on_err:
                return None

            raise ValueError(f"Value does not match pattern: {pattern.pattern}")

        return value

    return _validator
