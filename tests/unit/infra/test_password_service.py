import pytest

from src.app.infra.services.password_service import PasswordService

pytestmark = [pytest.mark.unit, pytest.mark.infra]


class TestPasswordService:
    def test_round_trip(self, password_service: PasswordService):
        hashed = password_service.hash_password("s3cret-passphrase")

        assert password_service.verify_password("s3cret-passphrase", hashed)
        assert not password_service.verify_password("wrong", hashed)

    def test_empty_hash_never_verifies(self, password_service: PasswordService):
        """An account with no usable password yet must not authenticate."""
        assert password_service.verify_password("anything", "") is False

    def test_rejects_over_long_passwords(self, password_service: PasswordService):
        # bcrypt truncates at 72 bytes; silently accepting a longer value would
        # let a prefix of it authenticate.
        with pytest.raises(ValueError):
            password_service.hash_password("x" * 73)

    def test_needs_rehash_for_foreign_hashes(self, password_service: PasswordService):
        assert password_service.needs_rehash("pbkdf2_sha256$260000$abc$def") is True
        assert (
            password_service.needs_rehash(password_service.hash_password("abc")) is False
        )
