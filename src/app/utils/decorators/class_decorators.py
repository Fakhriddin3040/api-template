from dataclasses import dataclass, field, Field
from typing import Any, Callable, dataclass_transform


@dataclass_transform(
    field_specifiers=(field, Field),
    kw_only_default=True,
)
def domain_params[T](**dc_kwargs: Any) -> Callable[[T], T]:
    def wrapper(cls: T) -> T:
        annotations = getattr(cls, "__annotations__", {})

        for name in annotations:
            if not hasattr(cls, name):
                setattr(cls, name, field(default=None, kw_only=True))

        dc_kwargs["frozen"] = True
        dc_kwargs["slots"] = True
        dc_kwargs["kw_only"] = True

        return dataclass(**dc_kwargs)(cls)  # type: ignore[return-value]

    return wrapper
