import pytest

from src.app.domain.identity.constants.consts import (
    OTP_CODE_LENGTH,
    otp_cooldown_minutes,
    otp_ttl_minutes,
)
from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.shared_kernel.utils.functions.security_funcs import generate_numeric_otp

pytestmark = [pytest.mark.unit, pytest.mark.application]


class TestNumericOtp:
    def test_has_the_configured_length(self):
        for _ in range(200):
            assert len(generate_numeric_otp(OTP_CODE_LENGTH)) == OTP_CODE_LENGTH

    def test_is_all_digits(self):
        assert generate_numeric_otp(OTP_CODE_LENGTH).isdigit()

    def test_zero_padding_keeps_the_length(self):
        """A leading zero must not shorten the code — the validator pins an
        exact length, and an unpadded value would be rejected as malformed."""
        assert len(generate_numeric_otp(1)) == 1
        assert all(len(generate_numeric_otp(4)) == 4 for _ in range(500))


class TestOtpPolicy:
    @pytest.mark.parametrize("kind", list(OtpKindEnum))
    def test_every_kind_has_a_ttl_and_cooldown(self, kind: OtpKindEnum):
        # A missing entry would raise KeyError deep inside the confirmation
        # service, at the moment a user is waiting on a code.
        assert otp_ttl_minutes(kind) > 0
        assert otp_cooldown_minutes(kind) > 0
