from typing import Union

import bcrypt

from src.app.shared_kernel.ports.security.password_proto import PasswordServiceProto
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)

_BCRYPT_PREFIXES = ("$2b$", "$2a$", "$2y$")

# bcrypt silently truncates at 72 bytes; rejecting instead of truncating keeps a
# long passphrase from verifying against a shorter prefix of itself.
_BCRYPT_MAX_BYTES = 72


class PasswordService(PasswordServiceProto):
    def hash_password(self, password: str) -> bytes:
        pwd_bytes = self.to_bytes(password)
        salt = self.generate_salt()
        return bcrypt.hashpw(password=pwd_bytes, salt=salt)

    def generate_salt(self) -> bytes:
        return bcrypt.gensalt()

    def needs_rehash(self, hashed_password: Union[str, bytes]) -> bool:
        """True when the stored hash was not produced by the current algorithm."""
        raw = (
            hashed_password
            if isinstance(hashed_password, str)
            else hashed_password.decode("utf-8")
        )
        return not raw.startswith(_BCRYPT_PREFIXES)

    def verify_password(
        self,
        password: Union[str, bytes],
        hashed_password: Union[str, bytes],
    ) -> bool:
        raw_str = password if isinstance(password, str) else password.decode("utf-8")
        hash_str = (
            hashed_password
            if isinstance(hashed_password, str)
            else hashed_password.decode("utf-8")
        )

        # An account that has no usable password yet (empty column) must never
        # verify — bcrypt would otherwise raise rather than answer False.
        if not hash_str.startswith(_BCRYPT_PREFIXES):
            return False

        try:
            return bcrypt.checkpw(
                password=self.to_bytes(raw_str),
                hashed_password=hash_str.encode("utf-8"),
            )
        except ValueError:
            return False

    def get_bytes(self, password: Union[str, bytes]) -> bytes:
        return password if isinstance(password, bytes) else self.to_bytes(password)

    def to_bytes(self, value: str) -> bytes:
        encoded = value.encode("utf-8")

        if len(encoded) > _BCRYPT_MAX_BYTES:
            raise ValueError(
                f"Password exceeds bcrypt's {_BCRYPT_MAX_BYTES}-byte limit"
            )

        return encoded


ensure_isimplementation(PasswordService, PasswordServiceProto)
