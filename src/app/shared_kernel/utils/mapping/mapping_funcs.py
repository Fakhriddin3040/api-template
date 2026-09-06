from dataclasses import is_dataclass, fields
from typing import Any, Callable, Dict, Type, Mapping

from pydantic import BaseModel

from src.app.shared_kernel.ports.domain.entity_proxy import EntityProxy


def map_obj_to_entity_proxy(
    src: Any,
    entity: EntityProxy,
    getter: Callable[[Any, str], Any] = getattr,
    prop_checker: Callable[[Any, str], bool] = hasattr,
) -> None:
    for f in entity._proxy_fields:  # noqa
        if prop_checker(src, f):
            setattr(entity, f, getter(src, f))


def map_data_to_obj(
    src: dict | Any, obj: Any, setter: Callable[[Any, str, Any], None] = setattr
) -> None:
    if isinstance(src, dict):
        for k, v in src.items():
            setter(obj, k, v)
    else:
        for k, v in src.items():
            if not k.startswith("_") and not callable(v):
                setter(obj, k, v)


def get_unincluded_data(
    src: BaseModel | Any,
    target: Type | Any,
) -> Dict[str, Any]:
    """
    Returns all data from 'src' which are not included in 'target'

    Args:
        src (BaseModel | Any): Source data.
        target (Type | Any): Target type/instance.
    Returns:
        Dict[str, Any]: All data from 'src' which are not included in 'target'
    """
    unincluded_data = {}
    if isinstance(src, BaseModel):
        get_fields = (f for f in src.model_fields.keys())
    elif is_dataclass(src):
        get_fields = (f.name for f in fields(src))  # noqa
    else:
        raise TypeError(
            f"src must be a dataclass or pydantic model. Given {type(src) if src is not type else src}"
        )

    if isinstance(target, Mapping):
        target_key = dict.get
    else:
        target_key = getattr

    for f in get_fields:
        unincluded_data[f] = target_key(src, f)

    return unincluded_data
