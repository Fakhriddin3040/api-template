from typing import Protocol, runtime_checkable, Optional


@runtime_checkable
class EncryptionServiceProto(Protocol):
    def encrypt(self, data: bytes, pub_data: Optional[bytes] = None) -> bytes:
        """Encrypts data and return encrypted data as bytes"""

    def decrypt(self, data: bytes) -> bytes:
        """Decrypts data and return decrypted data as bytes"""


@runtime_checkable
class SignatureServiceProto(Protocol):
    def sign(self, data: bytes, key: Optional[bytes] = None) -> bytes:
        """Signs data and return encrypted data as bytes

        Args:
            data (bytes): data to sign
            key (Optional[bytes]): key to sign with (optional) given key.
                If key is not provided, will be used server secret

        Returns:
            bytes: signature bytes
        """

    def verify(
        self, data: bytes, signature: bytes, key: Optional[bytes] = None
    ) -> bool:
        """Verifies data and return verification result

        Args:
            data (bytes): data to verify
            signature (bytes): signature to verify
            key (Optional[bytes]): key to verify with (optional) given key.
                If key is not provided, will be used server secret

        Returns:
            bool: verification result
        """

    def sign_dict(self, data: dict, key: Optional[bytes] = None) -> bytes:
        """Make a signature for a dictionary

        Args:
            data (dict): data to sign
            key (Optional[bytes]): key to sign with (optional) given key.
                If key is not provided, will be used server secret

        Returns:
            bytes: signature bytes
        """

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
