from types import MappingProxyType
from typing import Mapping

from src.app.domain.identity.constants.enums import OtpKindEnum

# How long a one-time code stays valid, per purpose. Both flows here mail a
# short numeric code the recipient types back, so the window is deliberately
# tight — it limits brute force without being shorter than a mail round trip.
_MINUTES_PER_HOUR = 60
_MINUTES_PER_DAY = 24 * _MINUTES_PER_HOUR

OTP_TTL_MINUTES_BY_KIND: Mapping[OtpKindEnum, int] = MappingProxyType(
    {
        OtpKindEnum.EMAIL_CONFIRMATION: 15,
        OtpKindEnum.FORGOT_PASSWORD: 15,
    }
)

# Minimum gap between two issues for the same (content, kind). Guards against a
# resend button being used to spam the recipient.
OTP_COOLDOWN_MINUTES_BY_KIND: Mapping[OtpKindEnum, int] = MappingProxyType(
    {
        OtpKindEnum.EMAIL_CONFIRMATION: 1,
        OtpKindEnum.FORGOT_PASSWORD: 1,
    }
)

# Digits in a mailed numeric code.
OTP_CODE_LENGTH = 6


def otp_ttl_minutes(kind: OtpKindEnum) -> int:
    return OTP_TTL_MINUTES_BY_KIND[kind]


def otp_cooldown_minutes(kind: OtpKindEnum) -> int:
    return OTP_COOLDOWN_MINUTES_BY_KIND[kind]
