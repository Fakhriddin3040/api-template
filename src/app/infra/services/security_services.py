import base64
import hmac
import hashlib
import json
import os

from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.app.shared_kernel.config.app_config import AppConfig
from src.app.shared_kernel.ports.services.encryption import (
    EncryptionServiceProto,
    SignatureServiceProto,
)
from src.app.shared_kernel.ports.services.secrets import SecretServiceProto
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)


class AESGCMEncryptionService(EncryptionServiceProto):
    def __init__(self, config: AppConfig) -> None:
        self._key = config.aes_key

        if len(self._key) != 32:
            raise ValueError(self.__class__.__name__ + " requires 32 byte key")

        self._aes = AESGCM(self._key)

    def encrypt(self, data: bytes, pub_data: Optional[bytes] = None) -> bytes:
        nonce = self._generate_nonce()

        return nonce + self._aes.encrypt(
            nonce=nonce, data=data, associated_data=pub_data
        )

    def _generate_nonce(self) -> bytes:
        return os.urandom(12)

    def decrypt(self, data: bytes, pub_data: Optional[bytes] = None) -> bytes:
        nonce = data[:12]
        ciphertext = data[12:]
        return self._aes.decrypt(nonce, ciphertext, pub_data)


class HmacSha256SignatureService(SignatureServiceProto):
    def __init__(self, config: AppConfig) -> None:
        self._secret = config.secret_key.encode("utf-8")

    def sign(self, data: bytes, key: Optional[bytes] = None) -> bytes:
        key = key or self._secret
        return hmac.new(key, data, hashlib.sha256).digest()

    def verify(
        self, data: bytes, signature: bytes, key: Optional[bytes] = None
    ) -> bool:
        key = key or self._secret
        return hmac.compare_digest(self.sign(data, key), signature)

    def sign_dict(self, data: dict, key: Optional[bytes] = None) -> bytes:
        """Make a signature for a dictionary

        Args:
            data (dict): data to sign
            key (Optional[bytes]): key to sign with (optional) given key.
                If key is not provided, will be used server secret

        Returns:
            bytes: signature bytes
        """
        key = key or self._secret
        data_bytes = self._dump_dict(data)
        return hmac.new(key, data_bytes, hashlib.sha256).digest()

    def verify_dict(
        self, data: dict, signature: bytes, key: Optional[bytes] = None
    ) -> bool:
        """Verify a dictionary
        Args:
            data (dict): data to verify
            signature (bytes): signature to verify
            key (Optional[bytes]): key to verify with (optional) given key.
                If key is not provided, will be used server secret
        Returns:
            bool: verification result
        """
        print("KEY: ", key)
        return self.verify(self._dump_dict(data), signature, key)

    def _dump_dict(self, data: dict) -> bytes:
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


class SecretService(SecretServiceProto):
    def generate(self, length: int) -> bytes:
        return os.urandom(length)

    def generate_b64(self, length: int, /) -> bytes:
        """Generates 64-bit random bytes and returns base64decoded string"""
        return base64.b64encode(os.urandom(length))


ensure_isimplementation(AESGCMEncryptionService, EncryptionServiceProto)
ensure_isimplementation(HmacSha256SignatureService, SignatureServiceProto)
