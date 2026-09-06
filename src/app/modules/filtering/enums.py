from enum import StrEnum


class FilterLookupEnum(StrEnum):
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    IN = "in"
    RANGE = "rn"
    SEARCH = "search"
    # Structured value parsed from a JSON query param; the compiler decides what
    # the payload means (e.g. char_values -> variant_id).
    JSON = "json"
