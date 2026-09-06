from typing import Dict

from src.app.shared_kernel.data_structures.mappings import NamedDict, TKey, TValue


def wrap_to_named_dict(src: Dict[TKey, TValue]) -> NamedDict[TKey, TValue]:
    return NamedDict(src)
