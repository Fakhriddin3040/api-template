import secrets
import string

_PASSWORD_ALPHABET = string.ascii_letters + string.digits
_PASSWORD_LENGTH = 12


def generate_password() -> str:
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(_PASSWORD_LENGTH))


def generate_numeric_otp(length: int) -> str:
    """A zero-padded numeric one-time code.

    ``secrets.randbelow`` (not ``random``) because the value is a credential;
    zero-padding keeps every issued code the same length, so a leading zero can
    never make one shorter than the validator expects.
    """
    return str(secrets.randbelow(10**length)).zfill(length)
