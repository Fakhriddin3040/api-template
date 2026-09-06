from typing import Annotated

from pydantic import StringConstraints

from src.app.domain.identity.identity_constraints import (
    OTP_MAX_LENGTH,
    OTP_MIN_LENGTH,
    USER_ADDRESS_MAX_LENGTH,
    USER_EMAIL_MAX_LENGTH,
    USER_EMAIL_MIN_LENGTH,
    USER_EMAIL_REGEX,
    USER_NAME_MAX_LENGTH,
    USER_NAME_MIN_LENGTH,
    USER_NAME_REGEX,
    USER_PASSWORD_MAX_LENGTH,
    USER_PASSWORD_MIN_LENGTH,
    USER_PHONE_MAX_LENGTH,
    USER_PHONE_MIN_LENGTH,
    USER_PHONE_REGEX,
)
from src.app.shared_kernel.pydantic.validators import regex_validator_factory

type ATUserName = Annotated[
    str,
    StringConstraints(
        min_length=USER_NAME_MIN_LENGTH,
        max_length=USER_NAME_MAX_LENGTH,
        strip_whitespace=True,
    ),
    regex_validator_factory(USER_NAME_REGEX, normalize=True),
]

type ATUserEmail = Annotated[
    str,
    StringConstraints(
        min_length=USER_EMAIL_MIN_LENGTH,
        max_length=USER_EMAIL_MAX_LENGTH,
        pattern=USER_EMAIL_REGEX.pattern,
        strip_whitespace=True,
        to_lower=True,
    ),
]

type ATPhone = Annotated[
    str,
    StringConstraints(
        min_length=USER_PHONE_MIN_LENGTH,
        max_length=USER_PHONE_MAX_LENGTH,
        pattern=USER_PHONE_REGEX.pattern,
        strip_whitespace=True,
    ),
]

# Deliberately only bounded in length: any further policy (character classes,
# breach lists) belongs to the concrete project, not to the template.
type ATPassword = Annotated[
    str,
    StringConstraints(
        min_length=USER_PASSWORD_MIN_LENGTH,
        max_length=USER_PASSWORD_MAX_LENGTH,
    ),
]

type ATAddress = Annotated[
    str, StringConstraints(max_length=USER_ADDRESS_MAX_LENGTH, strip_whitespace=True)
]

type ATOtp = Annotated[
    str,
    StringConstraints(
        min_length=OTP_MIN_LENGTH,
        max_length=OTP_MAX_LENGTH,
        strip_whitespace=True,
    ),
]
