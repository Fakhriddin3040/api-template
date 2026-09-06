from datetime import datetime
import pytz


def get_now_utc() -> datetime:
    return datetime.now(tz=pytz.UTC)
