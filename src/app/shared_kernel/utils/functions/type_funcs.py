from enum import Enum
from typing import Type, Tuple, Any


def tuple_from_enum(enm: Type[Enum]) -> Tuple[Any]:
    return tuple(enm.__members__.values())
