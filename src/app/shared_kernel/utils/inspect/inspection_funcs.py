from inspect import signature

from typing import Mapping, Any, Type

from src.app.shared_kernel.types.base_types import T


def construct_safely(cls: Type[T], data: Mapping[str, Any]) -> T:
    sig = signature(cls.__init__)
    params = sig.parameters

    allowed = {
        name
        for name, p in params.items()
        if name != "self" and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    }
    filtered = {k: v for k, v in data.items() if k in allowed}

    return cls(**filtered)
