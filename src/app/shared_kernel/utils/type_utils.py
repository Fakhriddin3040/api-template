import json
from datetime import date, time, datetime
from decimal import Decimal
from typing import Callable, Any, Optional


from src.app.shared_kernel.data_types import TypeEnum

_ENCODERS: dict[TypeEnum, Callable[[Any], bytes]] = {
    TypeEnum.PYDANTIC_MODEL: lambda x: x.model_dump_json().encode(),
    TypeEnum.STRING: lambda x: x.encode(),
    TypeEnum.INTEGER: lambda x: str(x).encode(),
    TypeEnum.FLOAT: lambda x: str(x).encode(),
    TypeEnum.DECIMAL: lambda x: str(x).encode(),
    TypeEnum.NUMBER: lambda x: str(x).encode(),
    TypeEnum.DATE: lambda x: x.isoformat().encode(),
    TypeEnum.TIME: lambda x: x.isoformat().encode(),
    TypeEnum.DATE_TIME: lambda x: x.isoformat().encode(),
    TypeEnum.BOOL: lambda x: str(int(x)).encode(),
    TypeEnum.CHAR: lambda x: str(x).encode(),
    TypeEnum.DICT: lambda x: json.dumps(x).encode(),
}


_DECODERS: dict[TypeEnum, Callable[..., Any]] = {
    TypeEnum.PYDANTIC_MODEL: lambda v, t: t.model_validate_json(v),
    TypeEnum.STRING: lambda v, t=None: v.decode(),
    TypeEnum.INTEGER: lambda v, t=None: int(v.decode()),
    TypeEnum.FLOAT: lambda v, t=None: float(v.decode()),
    TypeEnum.DECIMAL: lambda v, t=None: Decimal(v.decode()),
    TypeEnum.NUMBER: lambda v, t=None: float(v.decode()),
    TypeEnum.DATE: lambda v, t=None: date.fromisoformat(v.decode()),
    TypeEnum.TIME: lambda v, t=None: time.fromisoformat(v.decode()),
    TypeEnum.DATE_TIME: lambda v, t=None: datetime.fromisoformat(v.decode()),
    TypeEnum.BOOL: lambda v, t=None: bool(int(v.decode())),
    TypeEnum.CHAR: lambda v, t=None: v.decode(),
    TypeEnum.DICT: lambda v, t=None: json.loads(v.decode()),
}

class _TypeCodec:
    @staticmethod
    def encode(obj: Any, type_const: TypeEnum) -> bytes:
        return _ENCODERS[type_const](obj)

    @staticmethod
    def decode[T: Any](data: bytes, type_const: TypeEnum, typ: Optional[type] = None) -> T:
        return _DECODERS[type_const](data, typ)
