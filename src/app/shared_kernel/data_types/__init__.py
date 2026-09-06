from enum import Enum



class TypeEnum(Enum):
    """Custom types as const enum"""
    JSON_OBJECT = 1
    PYDANTIC_MODEL = 2
    DICT = 3
    STRING = 4
    INTEGER = 5
    FLOAT = 6
    DECIMAL = 7
    NUMBER = 8
    BOOL = 9
    CHAR = 10
    DATE = 11
    DATE_TIME = 12
    TIME = 13
