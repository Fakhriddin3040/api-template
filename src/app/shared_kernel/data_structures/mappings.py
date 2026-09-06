from typing import Optional, Any, TypeVar, Generic

TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


class NamedDict(Generic[TKey, TValue], dict[TKey, TValue]):
    def __init__(self, obj: Optional[Any] = None, **kwargs):
        super().__init__(**kwargs)

        if not obj:
            return

        if isinstance(obj, NamedDict):
            self.update(**obj)
        else:
            slots = obj.__slots__ or (obj, "__dict__")

            if isinstance(slots, dict):
                self.__init__(self, **slots)
            elif isinstance(slots, (list, tuple)):
                self.__init__(self, **{slot: getattr(obj, slot) for slot in slots})

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value
