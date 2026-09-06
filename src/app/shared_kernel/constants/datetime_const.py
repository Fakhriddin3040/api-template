from pytz import timezone, utc

# Fallback when APP_TIMEZONE is unset. UTC, not a local zone: a template that
# defaults to somebody's city silently shifts every timestamp in a fork.
DEFAULT_TIMEZONE = utc


def resolve_timezone(name: str):
    """A tzinfo for an IANA zone name, e.g. ``Europe/Berlin``."""
    return timezone(name)
