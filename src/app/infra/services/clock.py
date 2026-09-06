from datetime import datetime, tzinfo
from typing import Optional

import pytz

from src.app.shared_kernel.ports.services import ClockProto


class Clock(ClockProto):
    def __init__(self, tz_: tzinfo) -> None:
        self._tz = tz_

    @staticmethod
    def get_utc() -> datetime:
        return datetime.now(pytz.utc)

    @staticmethod
    def get_utc_epoch() -> float:
        return datetime.now().timestamp()

    def get_now(self, tz: Optional[tzinfo] = None) -> datetime:
        return datetime.now(tz=self._tz)

    def get_now_epoch(self, tz: Optional[tzinfo] = None) -> float:
        return self.get_now().timestamp()

    def get_current_timezone(self) -> tzinfo:
        return self._tz
