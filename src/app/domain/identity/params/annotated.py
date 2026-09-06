"""Domain value types for identity.

These live in the domain, not the application layer, because the constraints are
the domain's: an email is an email whether it arrives from HTTP, a CLI seed or a
test. Commands and domain params both annotate with them, so a rule is written
once and enforced at every entry point.
"""

from typing import Annotated

from pydantic import AfterValidator, StringConstraints

from src.app.domain.identity.identity_constraints import (
    OTP_MAX_LENGTH,
    OTP_MIN_LENGTH,
    USER_ADDRESS_MAX_LENGTH,
    USER_DESCRIPTION_MAX_LENGTH,
    USER_EMAIL_MAX_LENGTH,
    USER_EMAIL_MIN_LENGTH,
    USER_EMAIL_REGEX,
    USER_INFORMATION_MAX_LENGTH,
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
    # Must be wrapped in AfterValidator: a bare callable in the metadata is
    # metadata, and pydantic ignores it — which is how this regex silently went
    # unenforced before.
    #
    # Normalises unicode and strips zero-width characters before matching, so a
    # name pasted from a rich-text editor is not rejected for invisible reasons.
    AfterValidator(regex_validator_factory(USER_NAME_REGEX, normalize=True)),
]

type ATUserEmail = Annotated[
    str,
    StringConstraints(
        min_length=USER_EMAIL_MIN_LENGTH,
        max_length=USER_EMAIL_MAX_LENGTH,
        pattern=USER_EMAIL_REGEX.pattern,
        strip_whitespace=True,
        # The login credential is looked up by exact match, so it is normalised
        # on the way in rather than lower-cased at every call site.
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

type ATDescription = Annotated[
    str, StringConstraints(max_length=USER_DESCRIPTION_MAX_LENGTH)
]

type ATInformation = Annotated[
    str, StringConstraints(max_length=USER_INFORMATION_MAX_LENGTH)
]

type ATOtp = Annotated[
    str,
    StringConstraints(
        min_length=OTP_MIN_LENGTH,
        max_length=OTP_MAX_LENGTH,
        strip_whitespace=True,
    ),
]
